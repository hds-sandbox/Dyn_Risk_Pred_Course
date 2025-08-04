# Packages
library(ggplot2)
library(tidyverse)
library(tidymodels)

# Basic pre-coding
options(scipen = 999) # removes scientific notation (0 to redo it)

setwd("~/Dyn_Risk_Pred_Course/lectures/exercise_solutions")
source("request_fhir.R")


base <- 'https://test/fhir'

#### Task 1: List patients using the get method from requests_fhir ####

# Getting the entire list of patients out
patient_list <- get_r(paste0(base, "/Patient"))

patient_df <- fromJSON(patient_list$content, flatten = T)$entry %>%
  select(id = resource.id,
         sex = resource.gender,
         d.birth = resource.birthDate) %>% 
  mutate(id = as.numeric(id))
patient_df


#### Task 2: Look at the snomed.csv file inside the data folder to see which code to use to access the data ####
snomed <- read.csv("data/snomed.csv") 
# Full code list and corresponding label
snomed %>% select(code,label)
# Quick translation using diag data set
dict <- read.csv("Data/dict_data.csv")
snomed[30:32,"label"] <- dict$diag


#### Task 3: Get measurements of cholesterol for a patient and plot it over time ####
patient_id_to_fetch <- 4
# Cholesterol code
chol_code <- snomed %>% filter(label == "chol") %>% select(code)

chol_url <- paste0(base, "/Observation?patient=", patient_id_to_fetch, "&code=", chol_code)

chol_list <- get_r(chol_url)
chol_df <- fromJSON(chol_list$content, flatten = T)$entry %>%
  select(time = resource.effectiveDateTime,
         value = resource.valueQuantity.value)
chol_df

ggplot(chol_df, aes(x = as.POSIXct(time), y = value, group = 1)) +
  geom_line(color = "steelblue") +
  geom_point(color = "red") +
  # change the tick placement and labels
  scale_x_continuous(breaks = as.POSIXct(ymd(year(chol_df$time), truncated = 2L)),
                     labels = year(chol_df$time)) + 
  # Axis labels and title
  labs(
    title = paste("Cholesterol Levels for Patient ID:", patient_id_to_fetch),
    x = "Year of Measurement",
    y = "Cholesterol Value (mmol/L or mg/dL - check units)"
  ) +
  theme_minimal()


#### Task 4: Obtain the necessary information for your model using requests_fhir ####
# For the model in the course we need:
# "id"           "date"         "systolic"     "diastolic"    "erythrocytes" "hemoglobin"   
# "wbc"          "platelets"    "glucose"      "potassium"    "creatine"     "chol"      
# "hdl"          "ldl"          "cvscore"      "diag"         "anxiety"      "sleep"       
# "alcohol"      "fruit"        "vegetable"    "aspirin"      "clopridrogel" "anticlot" 
# "ezetimibe"    "statins"      "visit"        "sex"          "d.birth"      "smoking"  
# "event"        "split"  
# and then it needs to go through the same data management as before

# run the data management code (mainly to get summaries, functions and predictor names)
source("~/Dyn_Risk_Pred_Course/lectures/exercise_solutions/Workshop 1 - data management.R", echo=F)

snomed <- snomed %>% filter(label %in% c(colnames(final_data),colnames(timevar), "smoker",
                                         "revascularization", "malignancy", "stroke",
                                         "amputation", "infarction"))

# Here only (approx.) a quarter of the real data is used to limit fetch time
set.seed(2025)
ids <- patient_df$id %>% sample(length(patient_df$id)/4) %>% paste0(collapse = ",")


### Get data from "Observation" database ###
obs_codes_for_url <- snomed %>%
  filter(source %in% c("blood_data",
                       "quest_data",
                       "diag_data",
                       "visit_date",
                       "baseline_data")) %>% 
  select(code) %>%
  unlist()

for(code in obs_codes_for_url){
  if(code == obs_codes_for_url[1]){
    obs_df <- c()
  }
  tmp_url <- paste0(base, "/Observation?patient=", ids, "&code=", code)
  
  tmp_list <- get_r(tmp_url)
  
  tmp_df <- fromJSON(tmp_list$content, flatten = T)$entry %>%
    select(id = resource.subject.reference,
           date = resource.effectiveDateTime,
           value = resource.valueQuantity.value) %>% 
    mutate(id = gsub("Patient/", "", id),
           across(all_of(colnames(.)), ~case_when(. == "null" ~ NA, T ~ .)))
  
  if(ncol(tmp_df) == 3){
    # Change variable name
    var_nam = snomed$label[snomed$code == code]
    
    colnames(tmp_df) <- c("id", "date", var_nam)
  }
  
  # Convert some columns from strings to numberic values
  tmp_df <- tmp_df %>%
    mutate(across(all_of(setdiff(colnames(.), c("date", "visit", "smoker"))), as.numeric))
  
  if(code == obs_codes_for_url[1]){
    obs_df <- tmp_df
  } else {
    obs_df <- full_join(obs_df, tmp_df, by = c("id", "date")) %>% arrange(id, date)
  }
}

### Get data from "Procedure" database ###
pro_codes_for_url <- snomed %>% filter(source %in% c("treat_data","events")) %>% 
  select(code) %>%
  unlist()

for(code in pro_codes_for_url){
  if(code == pro_codes_for_url[1]){
    pro_df <- c()
  }
  tmp_url <- paste0(base, "/Procedure?patient=", ids, "&code=", code)
  
  tmp_list <- get_r(tmp_url)
  
  tmp_df <- fromJSON(tmp_list$content, flatten = T)$entry %>%
    select(id = resource.subject.reference,
           date = resource.performedDateTime,
           value = resource.valueQuantity.value) %>% 
    mutate(id = gsub("Patient/", "", id),
           across(all_of(colnames(.)), ~case_when(. == "null" ~ NA, T ~ .)),
           across(all_of(setdiff(colnames(.), "date")), as.numeric))
  
  if(ncol(tmp_df) == 3){
    # Change variable name
    var_nam = snomed$label[snomed$code == code]
    
    colnames(tmp_df) <- c("id", "date", var_nam)
  }
  
  if(code == pro_codes_for_url[1]){
    pro_df <- tmp_df
  } else {
    pro_df <- full_join(pro_df, tmp_df, by = c("id", "date"), multiple = "all") %>% arrange(id, date)
  }
}

# Combine it at the end
newdata <- pro_df %>%
  fill(aspirin:statins, .direction = "down") %>% 
  mutate(across(aspirin:statins, function(x){x[is.na(x)] <- mean(x, na.rm = T); return(x)})) %>% 
  full_join(obs_df, multiple = "all", by = c("id","date")) %>% 
  left_join(patient_df, by = "id") %>%
  mutate(date = as.POSIXlt(date, tz = "UTC")) %>%
  arrange(id,date)

# Copy-paste the final part of data management with slight adjustments
new_final_data <-
  newdata %>% 
  arrange(id, date) %>% 
  # Prediction time points, age and encoding of sex and smoking
  mutate(visit          = if_else(is.na(visit), F, T),
         age            = interval(d.birth, date) / years(1), 
         male           = if_else(sex == "male", 1, 0), 
         smoker_current = if_else(smoker == "current", 1, 0), 
         smoker_former  = if_else(smoker == "former", 1, 0)) %>% 
  # One-hot encoding of diagnoses and events - using carry-forward approach
  group_by(id) %>% 
  mutate(across(c(diabetes, hyperlipidemia, hypertension), ~ case_when(is.na(.) ~ 0, T ~ 1)),
         across(c(diabetes, hyperlipidemia, hypertension), cumsum),
         across(revascularization:stroke, ~ case_when(is.na(.) ~ 0, T ~ 1))) %>% 
  # Calculating some summary variables for the cumulated (countable) variables
  mutate(across(revascularization:stroke, cumsum, .names = "n_{.col}"),
         across(revascularization:stroke, ~ func_nyears(., sum, date, n_years),
                .names = "nyear_{.col}"),
         n_treatments     = case_when(is.na(clopidogrel) ~ 0, # this ensures 0s at times where no treatment observations are found
                                      T ~ clopidogrel + ezetimibe + anticlot + aspirin + statins),
         nyear_treatments = func_nyears(n_treatments, sum, date, n_years),
         n_treatments     = cumsum(n_treatments)) %>%  
  select(-d.birth, -sex, -smoker, -revascularization, -malignancy, -stroke, -amputation, -infarction) %>% 
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
  ungroup() %>% 
  # Prediction time points only
  filter(visit) %>% 
  select(-visit) %>% 
  # Change from last prediction time in the quest data set variables
  group_by(id) %>% 
  # Difference in the questionnaire answers from visit to visit (summary variable)
  mutate(across(anxiety:vegetable, ~ c(0,diff(.)), .names = "diff_{.col}")) %>% 
  ungroup() %>% 
  # Normalise values
  mutate(across(-c(id, date),
                ~ (. - fin_sum[[paste0("min_",  cur_column())]]) /
                  (fin_sum[[paste0("max_", cur_column())]] - fin_sum[[paste0("min_",  cur_column())]])))


#### Task 5: Feed these data into your trained model and make predictions ####
# Load a previously trained model (in our case it is the boosting model)
mod <- read_rds("trained_model.RDS")

mod %>%
  extract_workflow() %>% 
  predict(new_data = new_final_data, type = "prob") %>%
  select(.pred_1) %>%
  unlist() %>%
  hist(breaks = 200, main = "Histogram of predicted probabilities")