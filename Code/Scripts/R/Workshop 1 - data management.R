library(tidyverse)
library(rstudioapi)

# Getting the path of your current open file
current_path = rstudioapi::getActiveDocumentContext()$path 
setwd(dirname(current_path ))
print( getwd() )

options(dplyr.width = Inf)
## -----------------------------------------------------------------------------
## Load data
## -----------------------------------------------------------------------------

# Data should be saved in a folder named "Data" in the working directory

baseline <- read.csv("Data/baseline_data.csv")
diag     <- read.csv("Data/diag_data.csv") %>% select(-X)
dict     <- read.csv("Data/dict_data.csv") %>% select(-X)
quest    <- read.csv("Data/quest_data.csv") %>% select(-X)


blood <- 
  read.csv("Data/blood_data.csv") %>% 
  select(-X) %>% 
  rename(id = ..record.id)

treat <- 
  read.csv("Data/treat_data.csv") %>% 
  select(-X) %>% 
  rename(id = record_id)

visits <- 
  read.csv("Data/visit_date.csv") %>% 
  select(id, date = visit_date) %>% 
  mutate(visit = T)

events <- 
  read.csv("Data/events.csv") 


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
  select_if(~ mean(is.na(.)) < 0.2)

table(diag$diag)

print(dim(baseline))
print(dim(blood))
print(dim(quest))
print(dim(treat))
print(dim(diag))


column_counts <- sapply(quest, function(column) sum(!is.na(column)))

# Print the counts
print(column_counts)

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

# Merge data - one row per time stamp
timevar <- 
  full_join(blood, diag, multiple = "all", by = c("id", "sample_date")) 
print("After full_join(blood, diag)")
print(timevar)
print(dim(timevar))

timevar <- timevar %>%
  full_join(quest, multiple = "all", by = c("id", "sample_date" = "date.x"))
print("After full_join(quest)")
print(timevar)
print(dim(timevar))

timevar <- timevar %>%
  full_join(treat, multiple = "all", by = c("id", "sample_date" = "treat_start_date"))
print("After full_join(treat)")
print(timevar)
print(dim(timevar))


timevar <- timevar %>%
  full_join(visits, multiple = "all", by = c("id", "sample_date" = "date"))
print("After full_join(visits)")
print(timevar)
print(dim(timevar))

timevar <- timevar %>%
  full_join(baseline, multiple = "all", by = "id")
print("After full_join(baseline)")
print(timevar)
print(dim(timevar))

timevar <- timevar %>%
  rename(date = sample_date)
print("After renaming")
print(timevar)
print(dim(timevar))

timevar <- timevar %>%
  left_join(splits, by = "id")
print("After left_join(splits)")
print(timevar)
print(dim(timevar))



# Count non-NA values in each column
column_counts <- sapply(timevar, function(column) sum(!is.na(column)))

# Print the counts
print(column_counts)

## -----------------------------------------------------------------------------
## Mean values and standard deviation for imputation and normalisation 
## -----------------------------------------------------------------------------

# Step 1: Filter rows where 'split' is "train"
filtered_data <- timevar %>%
  filter(split == "train")

print("Filtered Data:")
print(filtered_data)
dimensions <- dim(filtered_data)
print(dimensions)

# Step 2: Remove the 'diag' column
data_without_diag <- filtered_data %>%
  select(-diag)

print("Data without diag:")
print(data_without_diag)

# Step 3: Calculate means for specified columns
mean_columns <- data_without_diag %>%
  summarise(across(c(erythrocytes, wbc, glucose, potassium, chol, hdl, ldl, cvscore),
                   ~ mean(., na.rm = TRUE),
                   .names = "mean_{.col}"),
            across(c(systolic, diastolic, hemoglobin, platelets, creatine,
                     anxiety:vegetable, aspirin:statins),
                   ~ round(mean(., na.rm = TRUE)),
                   .names = "mean_{.col}"))

print("Mean Columns:")
print(mean_columns)

# Step 4: Calculate 1st quantiles (p = 0.01) for specified columns
q1_columns <- data_without_diag %>%
  summarise(across(systolic:statins,
                   ~ quantile(., p = 0.01, na.rm = TRUE),
                   .names = "q1_{.col}"))

print("Q1 Columns:")
print(q1_columns)

# Step 5: Calculate 99th quantiles (p = 0.99) for specified columns
q99_columns <- data_without_diag %>%
  summarise(across(systolic:statins,
                   ~ quantile(., p = 0.99, na.rm = TRUE),
                   .names = "q99_{.col}"))

print("Q99 Columns:")
print(q99_columns)

# Combine all the summaries
summaries <- cbind(mean_columns, q1_columns, q99_columns)

print("Final Summaries:")
print(summaries)


## -----------------------------------------------------------------------------
## Feature engineering
## -----------------------------------------------------------------------------




# Load necessary libraries
library(dplyr)
library(lubridate)

# Print original data
print("Original Data:")
print(timevar)

# Step 1: Arrange data by id and date
final_data <- timevar %>% 
  arrange(id, date)

# Print data after arranging
print("Data after arranging:")
print(final_data)

# Step 2: Mutation - Prediction time points, age, and encoding of sex and smoking
final_data <- final_data %>%
  mutate(visit = if_else(is.na(visit), F, visit),
         age = interval(d.birth, date) / years(1),
         male = if_else(sex == "male", 1, 0),
         smoker_current = if_else(smoking == "current", 1, 0),
         smoker_former = if_else(smoking == "former", 1, 0))

# Print data after mutation
print("Data after mutation:")
print(final_data)

# Step 3: Grouping and one-hot encoding of diagnoses
final_data <- final_data %>%
  group_by(id) %>%
  mutate(diabetes = case_when(diag == "diabetes" ~ 1, T ~ 0),
         hyperlipidemia = case_when(diag == "hyperlipidemia" ~ 1, T ~ 0),
         hypertension = case_when(diag == "hypertension" ~ 1, T ~ 0),
         across(c(diabetes, hyperlipidemia, hypertension), ~ cumsum(.)))

# Print data after grouping and one-hot encoding
print("Data after grouping and one-hot encoding:")
print(final_data)

# Step 4: Select columns to keep and fill missing values
final_data <- final_data %>%
  select(-diag, -d.birth, -sex, -smoking) %>%
  fill(systolic:statins, .direction = "down") %>%
  ungroup()

# Print data after column selection and filling missing values
print("Data after column selection and filling missing values:")
print(final_data)

# Step 5: Replace missing values with means from training data
final_data <- final_data %>%
  replace_na(as.list(summaries %>%
                       select(starts_with("mean")) %>%
                       rename_with(~str_replace(., "mean_", ""))))

# Print data after replacing missing values with means
print("Data after replacing missing values with means:")
print(final_data)


# Step 6: Cap and normalize values
final_data <- final_data %>%
  mutate(across(systolic:statins, ~ pmax(., summaries[[paste0("q1_", cur_column())]])),
         across(systolic:statins, ~ pmin(., summaries[[paste0("q99_", cur_column())]])),
         across(systolic:statins, ~ (. - min(., na.rm = T)) / (max(., na.rm = T) - min(., na.rm = T))))

# Print data after capping and normalizing values
print("Data after capping and normalizing values:")
print(final_data)

# Step 7: Filter and select relevant columns
final_data <- final_data %>%
  filter(visit) %>%
  select(-visit) %>%
  relocate(split, .after = id)

# Print data after filtering and selecting columns
print("Data after filtering and selecting columns:")
print(final_data)

# Step 8: Join with events data and calculate 1-year mortality
final_data <- final_data %>%
  left_join(events %>%
              filter(type == "death") %>%
              rename(d.death = date) %>%
              select(d.death, id), by = "id") %>%
  mutate(died_1y = case_when(interval(date, d.death) / years(1) <= 1 ~ 1,
                             T ~ 0))

# Print data after joining with events and calculating 1-year mortality
print("Data after joining with events and calculating 1-year mortality:")
print(final_data)

# Step 9: Select final columns
final_data <- final_data %>%
  select(-d.death)

# Print final data
print("Final Data:")
print(final_data)

# Summary of final_data
summary(final_data)



## -----------------------------------------------------------------------------
## Data prepared for workshop 2
## -----------------------------------------------------------------------------
write.csv(final_data, ("Data_ready_for_workshop2_R.csv"), row.names = F)
final_data

