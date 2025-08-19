library(tidyverse)
library(slider)

## -----------------------------------------------------------------------------
## Funky functions
## -----------------------------------------------------------------------------
func_nyears = function(x, .f, date, interval, ...){
  # Uses the function .f on all observations within (interval) years prior to
  # each individual observation in x
  res = rep(0,length(x))
  ints = interval(date, date)
  
  for(i in 1:length(x)){
    int_xi = interval(date[i] %m-% years(interval), date[i])
    index = int_overlaps(int_xi, ints)
    res[i] = .f(x[index], ...)
  }
  return(res)
}


## -----------------------------------------------------------------------------
## Load data
## -----------------------------------------------------------------------------

# Data should be saved in a folder named "Data" in the working directory
n_years <- 1

baseline <- read.csv("data/baseline_data.csv")
diag     <- read.csv("data/diag_data.csv") %>% select(-X)
dict     <- read.csv("data/dict_data.csv") %>% select(-X)
quest    <- read.csv("data/quest_data.csv") %>% select(-X)

blood <- 
  read.csv("data/blood_data.csv") %>% 
  select(-X) %>% 
  rename(id = ..record.id)

treat <- 
  read.csv("data/treat_data.csv") %>% 
  select(-X) %>% 
  rename(id = record_id)

visits <- 
  read.csv("data/visit_date.csv") %>% 
  select(id, date = visit_date) %>% 
  mutate(visit = T)

events <- read.csv("data/events.csv") %>% 
  select(-X)

## -----------------------------------------------------------------------------
## Translate diagnosis codes
## -----------------------------------------------------------------------------

diag <- 
  diag %>% 
  left_join(dict, by = "code") %>% 
  select(-code)


## -----------------------------------------------------------------------------
## Removing variable with >20% missing (for a more rigorous approach
## this should be evaluated based on training data only, but here for simplicity 
## done on all available data)
## -----------------------------------------------------------------------------

baseline <- 
  baseline %>% 
  select_if(~ mean(is.na(.)) < 0.2)

blood <- 
  blood %>% 
  select_if(~ mean(is.na(.)) < 0.2)

quest <- 
  quest %>% 
  select_if(~ mean(is.na(.)) < 0.2)

treat <- 
  treat %>% 
  select_if(~ mean(is.na(.)) < 0.2) %>%
  fill(aspirin:statins, .direction = "down") %>% 
  mutate(across(aspirin:statins, function(x){x[is.na(x)] <- mean(x, na.rm = T); return(x)}))
# Note that NA's are filled in for the treat dataset already here
# This is useful when done before combining the data set


## -----------------------------------------------------------------------------
## Training, validation, calibration, and test set
## -----------------------------------------------------------------------------

set.seed(1306)

idx <- 
  sample(c("train", "validation", "calibration", "test"), 
         size = nrow(baseline), replace  = T, prob = c(0.8, 0.05, 0.05, 0.1)) 

splits <- tibble(id = baseline$id, split = idx) 

# OBS: here we have approximately an equal number of visits (=prediction 
# time points) per patient, so just splitting data on a patient-level. 


## -----------------------------------------------------------------------------
## One dataset with a row per time stamp to contain all observed features
## -----------------------------------------------------------------------------

timevar <- 
  # Merge data - one row per time stamp
  full_join(blood, diag, multiple = "all", by = c("id", "sample_date")) %>% 
  full_join(quest, multiple = "all", by = c("id", "sample_date" = "date.x")) %>% 
  full_join(treat, multiple = "all", by = c("id", "sample_date" = "treat_start_date")) %>% 
  full_join(visits, multiple = "all", by = c("id", "sample_date" = "date")) %>% 
  full_join(baseline, multiple = "all", by = "id") %>% 
  full_join(events %>% filter(type %in% c("minor","other","major")) %>% select(-"type"),
            multiple = "all", by = c("id","sample_date" = "date")) %>%
  rename(date = sample_date) %>% 
  left_join(splits, by = "id") %>%
  mutate(date = as.POSIXlt(date, tz = "UTC"),
         age = interval(d.birth, date) / years(1)) %>% 
  relocate(age, .after = statins) %>% 
  arrange(id,date)

# OBS: the date is made into a POSIXlt class, as these work well with intervals
# Very useful when creating dynamic variables (using the funky function)


## -----------------------------------------------------------------------------
## Mean values for imputation and quantile values for capping 
## -----------------------------------------------------------------------------

summaries <- 
  timevar %>% 
  filter(split == "train") %>% 
  select(-diag) %>% 
  summarise(across(systolic:age, 
                   ~ mean(., na.rm = T), 
                   .names = "mean_{.col}"),
            across(c(systolic, diastolic, hemoglobin,
                     platelets, creatine, anxiety:statins), 
                   ~ round(mean(., na.rm = T)), 
                   .names = "mean_{.col}"),
            across(systolic:age, 
                   ~ quantile(., p = 0.01, na.rm = T), 
                   .names = "q1_{.col}"), 
            across(systolic:age, 
                   ~ quantile(., p = 0.99, na.rm = T), 
                   .names = "q99_{.col}"))

# Note: q1 and q99 will be equal to min and max in the training set after
# capping


## -----------------------------------------------------------------------------
## Feature engineering
## -----------------------------------------------------------------------------

final_data <-
  timevar %>% 
  # Prediction time points and encoding of sex and smoking
  mutate(visit          = if_else(is.na(visit), F, visit), 
         male           = if_else(sex == "male", 1, 0), 
         smoker_current = if_else(smoking == "current", 1, 0), 
         smoker_former  = if_else(smoking == "former", 1, 0)) %>% 
  # One-hot encoding of diagnoses and events - using carry-forward approach
  group_by(id) %>% 
  mutate(diabetes          = case_when(diag  == "diabetes" ~ 1, T ~ 0), 
         hyperlipidemia    = case_when(diag  == "hyperlipidemia" ~ 1, T ~ 0), 
         hypertension      = case_when(diag  == "hypertension" ~ 1, T ~ 0),
         across(c(diabetes, hyperlipidemia, hypertension), cumsum),
         revascularization = case_when(event == "revascularization" ~ 1, T ~ 0),
         malignancy        = case_when(event == "malignancy" ~ 1, T ~ 0),
         stroke            = case_when(event == "stroke" ~ 1, T ~ 0),
         amputation        = case_when(event == "amputation" ~ 1, T ~ 0),
         infarction        = case_when(event == "infarction" ~ 1, T ~ 0)) %>% 
  # Calculating some summary variables for the cumulated (countable) variables
  mutate(across(revascularization:infarction, cumsum, .names = "n_{.col}"),
         across(revascularization:infarction, ~ func_nyears(., sum, date, n_years),
                .names = "nyear_{.col}"),
         n_treatments     = case_when(is.na(clopridrogel) ~ 0, # this ensures 0s at times where no treatment observations are found
                                      T ~ clopridrogel + ezetimibe + anticlot + aspirin + statins),
         nyear_treatments = func_nyears(n_treatments, sum, date, n_years),
         n_treatments     = cumsum(n_treatments)) %>% 
  select(-diag, -d.birth, -sex, -smoking, -event, -revascularization, -malignancy, -stroke, -amputation, -infarction) %>% 
  # Carry-forward approach for blood, treatment, and questionnaire data: 
  fill(everything(), .direction = "down") %>% 
  # If no value to carry forward, use mean from training data
  replace_na(as.list(summaries %>% 
                       select(starts_with("mean")) %>% 
                       rename_with(~str_replace(., "mean_", "")))) %>% 
  # Create summary variable on the blood dataset in the form x - mean(x) for each person
  mutate(across(systolic:cvscore, ~ slide_vec(., 
                                              .f = function(x){
                                                if(length(x) == 1){return(0)};
                                                tail(x,1) - mean(head(x,-1))},
                                              .before = Inf),
                .names = "diff_{.col}")) %>% 
  # Prediction time points only
  filter(visit) %>% 
  select(-visit) %>% 
  # Difference in the questionnaire answers from visit to visit (summary variable)
  mutate(across(anxiety:vegetable, ~ c(0, diff(.)), .names = "diff_{.col}")) %>% 
  # Outcome: n-year mortality with n defined at the start of the document
  left_join(events %>%
              filter(type == "death") %>% 
              slice_min(order_by = date, by = "id", with_ties = F) %>% 
              select(date, id) %>% 
              rename(d.event = date), by = "id") %>% 
  ungroup() %>% 
  # Create the response variable
  mutate(mevent_nyear = case_when(interval(date, d.event) / years(1) <= n_years ~ 1, 
                                  T ~ 0)) %>% 
  select(-d.event) %>% 
  relocate(split, .after = mevent_nyear)

# OBS: could further make some historical aggregates

# Could transform diastolic and systolic to a categorical variable using
# bp = case_when(diastolic <  80 & systolic < 120 ~ 0,
#                diastolic <  80 & systolic < 129 ~ 1,
#                diastolic <  89 | systolic < 139 ~ 2,
#                diastolic < 120 | systolic < 180 ~ 3,
#                T ~ 4)

# find summaries for all predictors (including the new summary variables)
fin_sum <- 
  final_data %>%
  filter(split == "train") %>% 
  select(-c(id, date, split)) %>% 
  summarise(across(everything(), ~ min(., na.rm = T), 
                   .names = "min_{.col}"), 
            across(-starts_with("min_"), ~ max(., na.rm = T), 
                   .names = "max_{.col}"))

# Normalize predictors
final_data <- final_data %>% 
  mutate(across(-c(id, split, date),
                ~ (. - fin_sum[[paste0("min_",  cur_column())]]) /
                  (fin_sum[[paste0("max_", cur_column())]] - fin_sum[[paste0("min_",  cur_column())]])))



# Note: as we have normalized using from the training set, the above
# scaling will correspond to using the min and max from the training set to scale.



## -----------------------------------------------------------------------------
## Data prepared for workshop 2
## -----------------------------------------------------------------------------
write.csv(final_data, "Data_ready_for_workshop2.csv", row.names = F)