snomed <- data.frame(
  source = c(
    "visit_date", "baseline_data", "blood_data", "blood_data", "blood_data", "blood_data", "blood_data", "blood_data",
    "blood_data", "blood_data", "blood_data", "blood_data", "blood_data", "blood_data", "blood_data",
    "blood_data", "blood_data","blood_data", "quest_data", "quest_data", "quest_data", "quest_data", "quest_data",
    "treat_data", "treat_data", "treat_data", "treat_data", "treat_data", "treat_data",
    "diag_data", "diag_data", "diag_data", "events", "events", "events", "events", "events"
  ),
  label = c(
    "visit", "smoker", "systolic", "diastolic", "erythrocytes", "hemoglobin",
    "hematocrit", "wbc", "platelets", "glucose", "potassium", "urea", "creatine",
    "crp", "chol", "hdl", "ldl", "cvscore", "anxiety", "sleep", "alcohol",
    "fruit", "vegetable", "aspirin", "clopidogrel", "anticlot", "ezetimibe",
    "statins", "ace", "DE10", "BZFC8A", "DE782", "revascularization", "malignancy",
    "infarction", "amputation", "stroke"
  ),
  code = c(
    866149003, 77176002, 271649006, 271650006, 397063002, 250228002, 365616005,
    767002, 277201004, 365811003, 365760004, 365755003, 14804003, 55235003,
    365793008, 166832000, 166833005, 197480006, 44186003, 365967005, 226452005,
    226448004, 271925006, 387458008, 449681000124101, 182764009, 409149004,
    315053009, 41549009, 73211009, 38341003, 55822004, 297183000, 1240414004,
    55641003, 81723002, 90096001
  ),
  stringsAsFactors = FALSE
)

# Append code to the URL
snomed$URL <- paste0("http://purl.bioontology.org/ontology/SNOMEDCT/", snomed$code)

write.csv(snomed, file = "snomed.csv")

treat <- read.csv("Data/treat_data.csv");treat
treat %>% 
  rename(clopidogrel = clopridrogel) %>% 
  select(-X)
write.csv(treat, file = "Data/treat_data.csv")

####### HTTP THINGS #########
#req <- request("http://purl.bioontology.org/ontology/SNOMEDCT/77176002")
#req <- req %>% req_headers("Accept" = "text/plain", "Content-type" = "application/json")
#resp <- req %>% req_perform()
