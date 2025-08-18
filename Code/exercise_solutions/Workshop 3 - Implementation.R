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