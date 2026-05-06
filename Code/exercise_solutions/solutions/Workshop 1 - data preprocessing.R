library(tidyverse)

## -----------------------------------------------------------------------------
## 1. Load data
## -----------------------------------------------------------------------------

# Data saved in a folder named "Raw_data" in the working directory

baseline <- read.csv("exercise_data/raw_data/baseline_data.csv")
diag     <- read.csv("exercise_data/raw_data/diag_data.csv")
dict     <- read.csv("exercise_data/raw_data/dict_data.csv") 
quest    <- read.csv("exercise_data/raw_data/quest_data.csv") 
blood    <- read.csv("exercise_data/raw_data/blood_data.csv") 
treat    <- read.csv("exercise_data/raw_data/treat_data.csv")
events   <- read.csv("exercise_data/raw_data/events.csv") 
visits   <- read.csv("exercise_data/raw_data/visit_date.csv")  


## -----------------------------------------------------------------------------
## 1. Translate diagnosis codes
## -----------------------------------------------------------------------------

diag <- 
  diag %>% 
  left_join(dict, by = "code") %>% 
  select(-code)


## -----------------------------------------------------------------------------
## 2. Join feature datasets and the visits data set
## -----------------------------------------------------------------------------

# Adds indicator "visit" (used later for filtering to visit times only)
visits$visit <- T

# Rename columns before joining
blood <- blood %>% rename(id = ..record.id)
treat <- treat %>% rename(id = record_id)
quest <- quest %>% rename(date = date.x)


# Merge data - one row per unique time stamp (per patient)
feat_merged <- 
  blood %>% 
  full_join(diag,     by = c("id", "sample_date")) %>% 
  full_join(quest,    by = c("id", "sample_date" = "date")) %>% 
  full_join(treat,    by = c("id", "sample_date" = "treat_start_date")) %>% 
  full_join(visits,   by = c("id", "sample_date" = "visit_date")) %>% 
  rename(date = sample_date) 

## -----------------------------------------------------------------------------
## 3. Add baseline information
## -----------------------------------------------------------------------------

full_dat <- 
  feat_merged %>% 
  full_join(baseline, by = "id") 

### SPØRG HEIDI OM DER ER EN MENING MED X.X, X.X.X, X.Y OSV 
full_dat <- full_dat %>% select(-matches("^X\\."))

set.seed(123)

idx <- 
  sample(c("train", "validation", "calibration", "test"), 
         size = nrow(baseline), replace  = T, prob = c(0.7, 0.1, 0.1, 0.1)) 

splits <- tibble(id = baseline$id, split = idx) 

# OBS: here we have approximately an equal number of visits (= prediction 
# time points) per patient, so just splitting data on patient-level. However,
# this approach does not ensure an equal proportion of positive outcomes across
# splits 

full_dat2 <- 
  full_dat %>% 
  left_join(splits, by = "id") 

  
## -----------------------------------------------------------------------------
## 5. Removing predictors with >20% missing, patient-level
## -----------------------------------------------------------------------------
feat_2keep <- 
  full_dat2 %>% 
  filter(split == "train") %>% 
  group_by(id) %>% 
  summarise(across(-date, ~ all(is.na(.)))) %>%
  select_if(~ mean(.) < 0.2) %>% 
  colnames

full_dat3 <- 
  full_dat2 %>% 
  select(id, date, all_of(feat_2keep))

## -----------------------------------------------------------------------------
## 5. Calculate age at each visit 
## -----------------------------------------------------------------------------

full_dat4 <- 
  full_dat3 %>% 
  # Calculate age at each visit
  mutate(age = interval(d.birth, date) / years(1)) %>% 
  # Convert integers to double 
  mutate(across(where(is.integer), as.double))  
  


## -----------------------------------------------------------------------------
## 5. Mean values and standard deviation for imputation and normalisation 
## -----------------------------------------------------------------------------

summaries <- 
  full_dat4 %>% 
  filter(split == "train") %>% 
  select(-diag) %>% 
  summarise(across(c(systolic:ace, age), 
                   ~ mean(., na.rm = T), 
                   .names = "mean_{.col}"), 
            across(c(systolic:ace, age), 
                   ~ quantile(., p = 0.01, na.rm = T), 
                   .names = "q1_{.col}"), 
            across(c(systolic:ace, age), 
                   ~ quantile(., p = 0.99, na.rm = T), 
                   .names = "q99_{.col}"))

# Note: q1 and q99 will be equal to min and max in the training set after
# capping


## -----------------------------------------------------------------------------
## 5. Imputation and feature engineering
## -----------------------------------------------------------------------------

feat_done <-   
  full_dat4 %>% 
  # Prediction time points and one-hot encoding of sex and smoking
  mutate(visit          = if_else(is.na(visit), F, visit),
         male           = if_else(sex == "male", 1, 0), 
         female         = if_else(sex == "female", 1, 0), 
         smoker_current = if_else(smoking == "current", 1, 0), 
         smoker_former  = if_else(smoking == "former",  1, 0), 
         smoker_never   = if_else(smoking == "never" ,  1, 0)) %>% 
  # One-hot encoding of diagnoses + carry-forward imputation
  arrange(id, date) %>% 
  group_by(id) %>% 
  mutate(diabetes       = case_when(diag == "diabetes"       ~ 1, T ~ 0), 
         hyperlipidemia = case_when(diag == "hyperlipidemia" ~ 1, T ~ 0), 
         hypertension   = case_when(diag == "hypertension"   ~ 1, T ~ 0), 
         across(c(diabetes, hyperlipidemia, hypertension), ~ cumsum(.))) %>% 
  select(-diag, -d.birth, -sex, -smoking) %>% 
  # Carry-forward imputation for blood, treatment, and questionnaire data
  fill(systolic:ace, .direction = "down") %>% 
  ungroup() %>% 
  # If no value to carry forward, use mean from training data
  replace_na(as.list(summaries  %>% 
                       select(starts_with("mean")) %>% 
                       rename_with(~str_replace(., "mean_", "")))) %>% 
  # Cap and min-max normalise values
  mutate(across(c(systolic:ace, age), ~ pmax(., summaries[[paste0("q1_",  cur_column())]])),
         across(c(systolic:ace, age), ~ pmin(., summaries[[paste0("q99_", cur_column())]])), 
         across(c(systolic:ace, age), ~ (. - min(., na.rm = T)) / (max(., na.rm = T) - min(., na.rm = T)))) 

## -----------------------------------------------------------------------------
## 6. Filter data to keep prediction time points + define outcome 
## -----------------------------------------------------------------------------

# Events of interest
event_oi <- 
  events %>% 
  filter(type %in% c("death", "major", "minor")) %>% 
  arrange(date) %>% 
  slice(1, .by = id) %>% 
  rename(d.event = date)

# Prediction time points only
pred_data <- 
  feat_done %>% 
  filter(visit) %>% 
  select(-visit) %>% 
  relocate(split, .after = id) 
  
  
# Outcome: major event or death within a 1 year
final_data <- 
  pred_data %>% 
  left_join(event_oi, by = "id") %>% 
  # Convert to date instead of character
  mutate(date = ymd(date), 
         d.event = ymd(d.event)) %>% 
  # Define outcome
  group_by(id, date) %>% 
  mutate(event_1y = any((d.event >= date) & (d.event <= date + years(1)), 
                        na.rm = T)) %>%
  ungroup() %>% 
  # One row per prediction time per patient
  distinct(id, date, .keep_all = T) %>% 
  # Outcome as factor
  mutate(event_1y = factor(as.integer(event_1y), levels = c(1, 0))) %>% 
  select(-d.event, -event, -type) 


# Note: as we have capped using q1 and q99 from the training set, the above
# scaling will correspond to using the min and max from the training set to scale.


# NB: could further make some historical aggregates and add presence features

# Summary of the final data
skimr::skim(final_data)

summary(final_data)

## -----------------------------------------------------------------------------
## Data prepared for workshop 2
## -----------------------------------------------------------------------------
write.csv(final_data, "Data_ready_for_workshop2_test.csv", row.names = F)  #### Change back so don't have "_test" in either 
saveRDS(final_data, "Data_ready_for_workshop2_test.rds") # preferred for R (save factor levels etc.) #### Change back so don't have "_test" in either 