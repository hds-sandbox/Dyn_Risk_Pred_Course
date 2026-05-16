PATH <- "~/Dyn_Risk_Pred_Course/Code/exercise_solutions/solutions"
source(paste0(PATH, "/request_fhir.R"))
library(jsonlite)
library(dplyr)

## EXERCISE 1
# 1.1
BASE_URL <- "https://test/fhir"

# 1.2
patients_url <- paste0(BASE_URL, "/Patient")

# 1.3
response <- get_r(patients_url)

# 1.4
parsed_data <- fromJSON(response$content)

# 1.5
resource <- parsed_data$entry$resource
patients_df <- data.frame(
  id = resource$id,
  gender = resource$gender,
  birthDate = resource$birthDate
)

## EXERCISE 2
snomed <- read.csv("~/Dyn_Risk_Pred_Course/exercise_data/raw_data/snomed.csv")
chol_std_code <- snomed$code[which(snomed$label == "chol")]
ldl_std_code <- snomed$code[which(snomed$label == "ldl")]

## EXERCISE 3
query <- paste0(BASE_URL, 
                "/Observation?patient=2&code=",
                chol_std_code)
response <- get_r(query)
parsed_data <- fromJSON(response$content)
resource <- parsed_data$entry$resource
obs_df <- data.frame(
  date = as.Date(resource$effectiveDateTime),
  cholesterol = as.numeric(resource$valueQuantity$value)
)

obs_df %>% plot(type = "l", panel.first = grid())
