library(httr)
library(jsonlite)
library(glue)
library(tidyverse)

BASE_URL <- 'https://test/fhir'
JSON_CONTENT_TYPE <- "application/json"
JSON_HEADERS <- list('Content-type' = JSON_CONTENT_TYPE, 'Accept' = 'text/plain')


RAW_PATIENT_STR <- paste0(
  '{{"resourceType":"Patient","id":"{id}","meta":{{"versionId":"1","lastUpdated":"2023-05-23T09:33:58.623+00:00","source":"#TxHlcnq3KZSdg567"}},',
  '"text":{{"status":"generated","div":"<div>Some HTML</div>"}},"identifier":[{{"system":"http://example.org","value":"002"}}],"gender":"{gender}",',
  '"birthDate":"{birthdate}"}}'
)

RAW_OBSERVATION_STR <- paste0(
  '{{"resourceType":"Observation","id":"{id}","meta":{{"versionId":"1","lastUpdated":"2023-04-19T10:00:27.158+00:00","source":"#2I8F1Uz63ty9AVBh"}},',
  '"code":{{"coding":[{{"system":"http://snomed.info/sct","code":"{code}"}}]}},"status":"final","subject":{{"reference":"Patient/{patient_id}"}},',
  '"effectiveDateTime":"{date}","valueQuantity":{{"value":"{value}"}}}}'
)

RAW_PROCEDURE_STR <- paste0(
  '{{"resourceType":"Procedure","id":"{id}","meta":{{"versionId":"1","lastUpdated":"2023-04-14T10:00:27.158+00:00","source":"#2I8F1Uzwdaty9AVBh"}},',
  '"code":{{"coding":[{{"system":"http://snomed.info/sct","code":"{code}"}}]}},"subject":{{"reference":"Patient/{patient_id}"}},',
  '"performedDateTime":"{date}","valueQuantity":{{"value":"{value}"}}}}'
)


RAW_ENTRY_START_STR <- '{{"fullUrl":"{base_url}/{entity}/{id}","resource":'

RAW_ENTRY_END_STR <- ',"search":{"mode":"match"}}' 

RAW_BUNDLE_STR <- paste0(
  '{{"resourceType":"Bundle","id":"{bundle_id}","meta":{{"lastUpdated":"{current_timestamp}"}},',
  '"type":"searchset","link":[{{"relation":"self","url":"{base_url}/{entity}{query_string}"}}],"entry":[{entries}]}}'
)


create_error_response <- function(status_code, error_type, message) {
  response <- list(
    status_code = status_code,
    content = jsonlite::toJSON(list(error = error_type, message = message), auto_unbox = TRUE)
  )
  return(stop(response))
}

post_r <- function(url, data, headers) {
  response <- list(
    status_code = NULL,
    content = NULL
  )
  
  if (!startsWith(url, BASE_URL)) {
    response$status_code <- 404
    response$content <- toJSON(list(error = "NOT_FOUND", message = "You are trying to contact an inexisting server, check your URL."), auto_unbox = TRUE)
    return(response)
  }
  
  content_type <- headers[['Content-type']]
  
  if (is.null(content_type)) {
    response$status_code <- 403
    response$content <- toJSON(list(error = "BAD_REQUEST", message = "It seems no content-type is defined."), auto_unbox = TRUE)
    return(response)
  } else if (content_type != JSON_CONTENT_TYPE) {
    response$status_code <- 403
    response$content <- toJSON(list(error = "METHOD_NOT_ALLOWED", message = "The content-type is not correct."), auto_unbox = TRUE)
    return(response)
  }
  
  
  data_list <- tryCatch({
    fromJSON(data)
  }, error = function(e) {
    response$status_code <- 400
    response$content <- toJSON(list(error = "BAD_REQUEST", message = paste("Invalid JSON data:", e$message)), auto_unbox = TRUE)
    return(NULL)
  })
  
  if(is.null(data_list) && !is.null(response$status_code)) {
    return(response)
  }
  
  object_id <- sample(1356:9871, 1)
  
  data_list$id <- object_id
  
  if (is.null(data_list$meta)) {
    data_list$meta <- list()
  }
  data_list$meta$versionId <- '1'
  data_list$meta$lastUpdated <- '2022-09-09T09:15:01.328000+00:00'
  
  if (is.null(data_list$text)) {
    data_list$text <- list()
  }
  data_list$text$status <- "generated"
  data_list$text$div <- paste0(
    "<div xmlns=\"http://www.w3.org/1999/xhtml\"><div class=\"hapiHeaderText\">Some object</div>",
    "<table class=\"hapiPropertyTable\"><tbody><tr><tr><td>Identifier</td><td>",
    object_id,
    "</td></tr></tbody></table></div>"
  )
  
  
  modified_data_json <- toJSON(data_list, auto_unbox = TRUE)
  
  # --- Success Response ---
  response$status_code <- 200
  response$content <- modified_data_json
  
  return(response)
}


get_r <- function(url) {
  response <- list(status_code = 200, content = NULL)
  
  if (!startsWith(url, BASE_URL)) {
    return(create_error_response(404, "NOT_FOUND", "You are trying to contact an inexisting server, check your URL."))
  }
  
  
  path_part <- str_remove(url, BASE_URL)
  path_part <- str_remove(path_part, "^/|/$")
  
  entity_with_info <- str_split(path_part, "/")[[1]]
  
  entity <- sub("\\?.*", "", entity_with_info[1])
  entity_id <- 0
  
  if (length(entity_with_info) >= 2 && nchar(entity_with_info[2]) > 0) {
    id_part <- sub("\\?.*", "", entity_with_info[2])
    if (nchar(id_part) > 0) {
      id_num <- suppressWarnings(as.numeric(id_part))
      if (!is.na(id_num)) {
        entity_id <- id_num
      } else {
      }
    }
  }
  
  tryCatch({
    baseline_df <- read_csv("data/baseline_data.csv",
                            col_types = cols(
                              id = col_double(),
                              sex = col_character(),
                              `d.birth` = col_date(format = ""),
                              smoking = col_character()
                            ), show_col_types = FALSE)
    snomed_df <- read_csv("data/snomed.csv",
                          col_types = cols(
                            code = col_double(),
                            label = col_character(),
                            source = col_character()
                          ), show_col_types = FALSE)
  }, error = function(e) {

    stop(glue("Error loading essential CSV files: {e$message}"))

  })

  if (!is.null(response$content) && response$status_code != 200) return(response)


  if (entity == 'Patient') {
    if (entity_id != 0) {
      patient_list <- baseline_df %>% filter(id == entity_id)

      if (nrow(patient_list) != 1) {
        return(create_error_response(404, "NOT_FOUND", "The patient was not found."))
      }

      patient_info <- patient_list %>% head(n = 1) #måske redundant

      patient_str <- glue(
        RAW_PATIENT_STR,
        id = patient_info$id,
        gender = patient_info$sex,
        birthdate = format(patient_info$`d.birth`, "%Y-%m-%d")
      )
      response$content <- patient_str
      return(response)

    } else {
      entries_list <- vector("list", nrow(baseline_df))
      for (i in 1:nrow(baseline_df)) {
        patient_info <- baseline_df[i, ]

        patient_body <- glue(
          RAW_PATIENT_STR,
          id = patient_info$id,
          gender = patient_info$sex,
          birthdate = format(patient_info$`d.birth`, "%Y-%m-%d")
        )
        temp_interpolated_start_str <- glue(
          RAW_ENTRY_START_STR,
          base_url = gsub("/$", "", BASE_URL),
          entity = entity,
          id = patient_info$id
        )
        entries_list[[i]] <- paste0(temp_interpolated_start_str, patient_body, RAW_ENTRY_END_STR)
      }

      entries_str <- paste(entries_list, collapse = ",\n")

      generated_bundle_id <- paste0("bundle-", sample(1356:9871, 1))
      formatted_timestamp <- strftime(Sys.time(), format = "%Y-%m-%dT%H:%M:%OS3Z", tz = "UTC")
      current_query_str <- "" # Initialize here

      bundle_str <- glue(
        RAW_BUNDLE_STR,
        bundle_id = generated_bundle_id,
        current_timestamp = formatted_timestamp,
        base_url = gsub("/$", "", BASE_URL),
        entity = entity,
        query_string = current_query_str,
        entries = entries_str
      )
      response$content <- bundle_str
      return(response)
    }
  } else if (entity == 'Observation' || entity == 'Procedure') {
    if (entity_id != 0) {
      return(create_error_response(501, "NOT_IMPLEMENTED", glue("You cannot fetch a {entity} using an ID.")))
    }

    parsed_url <- parse_url(url)
    query_params <- parsed_url$query

    if (is.null(query_params$patient) || is.null(query_params$code)) {
      return(create_error_response(501, "NOT_IMPLEMENTED", glue("You cannot request all {entity}s, please specify one or more patient IDs and one or more codes (e.g., ?patient=1,2&code=100,200).")))
    }

    patient_ids_str <- str_split(query_params$patient, ",")[[1]]
    snomed_codes_str <- str_split(query_params$code, ",")[[1]]

    patient_ids <- suppressWarnings(as.numeric(patient_ids_str))
    snomed_codes <- suppressWarnings(as.numeric(snomed_codes_str))

    if(any(is.na(patient_ids)) || any(is.na(snomed_codes))) {
      return(create_error_response(400, "BAD_REQUEST", "Invalid patient IDs or SNOMED codes provided. Ensure they are numeric."))
    }

    tryCatch({
      if (entity == 'Procedure') {
        treat_df <- read_csv("data/treat_data.csv",
                             col_types = cols(
                               id = col_double(),
                               treat_start_date = col_date(format = ""),
                               .default = col_guess()
                             ), show_col_types = FALSE)
        event_df <- read_csv("data/events.csv",
                             col_types = cols(
                               id = col_double(),
                               date = col_date(format = ""),
                               .default = col_guess()
                             ), show_col_types = FALSE) %>%
          filter(type != "death") %>%
          mutate(revascularization = case_when(event == "revascularization" ~ 1, T ~ 0),
                 malignancy        = case_when(event == "malignancy" ~ 1, T ~ 0),
                 infarction        = case_when(event == "infarction" ~ 1, T ~ 0),
                 amputation        = case_when(event == "amputation" ~ 1, T ~ 0),
                 stroke            = case_when(event == "stroke" ~ 1, T ~ 0))
      }
      if (entity == 'Observation') {
        blood_df <- read_csv("data/blood_data.csv",
                             col_types = cols(
                               `id` = col_double(),
                               sample_date = col_date(format = ""),
                               .default = col_guess()
                             ), show_col_types = FALSE)
        diag_df <- read_csv("data/diag_data.csv",
                            col_types = cols(
                              id = col_double(),
                              sample_date = col_date(format = ""),
                              code = col_character(),
                              .default = col_guess()
                            ), show_col_types = FALSE)
        quest_df <- read_csv("data/quest_data.csv",
                             col_types = cols(
                               id = col_double(),
                               `date` = col_date(format = ""),
                               .default = col_guess()
                             ), show_col_types = FALSE)
        visit_df <- read_csv("data/visit_date.csv",
                             col_types = cols(
                               id = col_double(),
                               visit_date = col_date(format = ""),
                               .default = col_guess()
                             ), show_col_types = FALSE)
      }
    }, error = function(e) {
      response <- create_error_response(500, "SERVER_ERROR", paste("Could not load data files for", entity, ":", e$message))
    })
    if (!is.null(response$content) && response$status_code != 200) return(response)


    entries_list_df <- list()

    param_grid <- expand.grid(patient_id = patient_ids, snomed_code = snomed_codes)

    for (i in 1:nrow(param_grid)) {
      p_id <- param_grid$patient_id[i]
      s_code <- param_grid$snomed_code[i]

      patient_list_df <- baseline_df %>% filter(id == p_id)
      if (nrow(patient_list_df) != 1) {
        return(create_error_response(404, "NOT_FOUND", glue("Patient with ID {p_id} was not found.")))
      }
      patient_info <- patient_list_df %>% head(n = 1)#måske overflødig

      snomed_list_df <- snomed_df %>% filter(code == s_code)
      if (nrow(snomed_list_df) != 1) {
        return(create_error_response(404, "NOT_FOUND", glue("SNOMED code {s_code} was not found.")))
      }
      snomed_info <- snomed_list_df %>% head(n = 1)#måske overflødig

      entries_temp_df <- NULL

      required_label <- snomed_info$label

      tryCatch({
        if (snomed_info$source == 'blood_data' && entity == 'Observation') {
          if (!required_label %in% names(blood_df)) next
          patient_blood_df <- blood_df %>%
            filter(`id` == p_id) %>%
            select(sample_date, all_of(required_label))
          if(nrow(patient_blood_df) > 0) {
            entries_temp_df <- patient_blood_df %>%
              rename(date = sample_date, value = all_of(required_label))
          }
        } else if (snomed_info$source == 'diag_data' && entity == 'Observation') {
          patient_diag_df <- diag_df %>%
            filter(id == p_id, code == required_label) %>%
            select(sample_date)
          if(nrow(patient_diag_df) > 0) {
            entries_temp_df <- patient_diag_df %>%
              mutate(value = 1) %>%
              rename(date = sample_date)
          }
        } else if (snomed_info$source == 'quest_data' && entity == 'Observation') {
          if (!required_label %in% names(quest_df)) next
          patient_quest_df <- quest_df %>%
            filter(id == p_id) %>%
            select(`date`, all_of(required_label))
          if(nrow(patient_quest_df) > 0) {
            entries_temp_df <- patient_quest_df %>%
              rename(date = `date`, value = all_of(required_label))
          }
        } else if (snomed_info$source == 'treat_data' && entity == 'Procedure') {
          if (!required_label %in% names(treat_df)) next
          patient_treat_df <- treat_df %>%
            filter(id == p_id) %>%
            select(treat_start_date, all_of(required_label))
          if(nrow(patient_treat_df) > 0) {
            entries_temp_df <- patient_treat_df %>%
              rename(date = treat_start_date, value = all_of(required_label))
          }
        } else if (snomed_info$source == 'events' && entity == 'Procedure') {
          if (!required_label %in% names(event_df)) next
          patient_event_df <- event_df %>%
            filter(id == p_id) %>%
            select(date, all_of(required_label))
          if(nrow(patient_event_df) > 0) {
            entries_temp_df <- patient_event_df %>%
              rename(value = all_of(required_label)) %>% 
              filter(value == 1)
          }
        } else if (snomed_info$source == 'baseline_data' && entity == 'Observation') {
          patient_visit_df <- visit_df %>%
            filter(id == p_id) %>%
            arrange(visit_date)
          if(nrow(patient_visit_df) > 0) {
            entries_temp_df <- patient_visit_df %>%
              mutate(value = patient_info$smoking) %>%
              select(visit_date, value) %>%
              rename(date = visit_date) %>% 
              head(n = 1)
          }
        } else if (snomed_info$source == 'visit_date' && entity == 'Observation') {
          patient_visit_df <- visit_df %>%
            filter(id == p_id) %>%
            arrange(visit_date)
          if(nrow(patient_visit_df) > 0) {
            entries_temp_df <- patient_visit_df %>%
              mutate(value = T) %>%
              select(visit_date, value) %>%
              rename(date = visit_date)
          }
        } else {
          valid_obs_source <- snomed_info$source %in% c('blood_data', 'diag_data', 'quest_data', 'baseline_data', "visit_date")
          valid_proc_source <- snomed_info$source %in% c('treat_data', 'events')
          if (! ( (entity == 'Observation' && valid_obs_source) || (entity == 'Procedure' && valid_proc_source) )) {
            
            return(create_error_response(501, "NOT_IMPLEMENTED", glue("Data source '{snomed_info$source}' for code {s_code} is not implemented or not applicable for {entity}.")))
          }
          
        }
      }, error = function(e) {
        warning(glue("Error processing patient {p_id}, code {s_code}: {e$message}"))
        entries_temp_df <- NULL # Ensure it's NULL on error
      })
      
      if (!is.null(entries_temp_df) && nrow(entries_temp_df) > 0) {
        if (!"value" %in% names(entries_temp_df)) entries_temp_df$value <- NA
        
        entries_temp_df <- entries_temp_df %>%
          mutate(
            code = s_code,
            patient_id = p_id,
            date_str = format(date, "%Y-%m-%d")
          ) %>%
          filter(!is.na(date_str) & !is.na(date))
        
        if(nrow(entries_temp_df) > 0) {
          entries_list_df[[length(entries_list_df) + 1]] <- entries_temp_df
        }
      }
    }
    if (length(entries_list_df) == 0) {
      entries_str <- ""
    } else {
      entries_df <- bind_rows(entries_list_df)
      
      if (nrow(entries_df) == 0) {
        entries_str <- ""
      } else {
        raw_entry_body_str <- if (entity == 'Observation') RAW_OBSERVATION_STR else RAW_PROCEDURE_STR
        
        entry_strings <- pmap_chr(entries_df, function(...) {
          entry_info <- list(...)
          entry_runtime_id <- paste0(entity,"-", entry_info$patient_id, "-", entry_info$code, "-", sample(1000:9999, 1)) # Dummy ID
          
          entry_body <- glue(
            raw_entry_body_str,
            id = entry_runtime_id,
            code = entry_info$code,
            patient_id = entry_info$patient_id,
            date = entry_info$date_str,
            value = ifelse(is.na(entry_info$value), "null", entry_info$value)
          )
          
          temp_interpolated_start <- glue(
            RAW_ENTRY_START_STR,
            base_url = gsub("/$", "", BASE_URL),
            entity = entity,
            id = entry_runtime_id
          )
          paste0(temp_interpolated_start, entry_body, RAW_ENTRY_END_STR)
        })
        entries_str <- paste(entry_strings, collapse = ",\n")
      }
    }
    
    generated_bundle_id <- paste0("bundle-", sample(1356:9871, 1))
    formatted_timestamp <- strftime(Sys.time(), format = "%Y-%m-%dT%H:%M:%OS3Z", tz = "UTC")
    
    current_query_str <- "" # Initialize here as well, before the if block
    
    if (!is.null(query_params) && length(query_params) > 0) {
      query_string_parts <- mapply(function(name, value) {
        paste0(URLencode(name), "=", URLencode(value))
      }, names(query_params), query_params, SIMPLIFY = TRUE, USE.NAMES = FALSE)
      current_query_string <- paste0("?", paste(query_string_parts, collapse = "&"))
    } else {
      current_query_string <- "" # Ensure it's an empty string if no params
    }
    
    
    bundle_str <- glue(
      RAW_BUNDLE_STR,
      bundle_id = generated_bundle_id,
      current_timestamp = formatted_timestamp,
      base_url = gsub("/$", "", BASE_URL),
      entity = entity,
      query_string = current_query_string, # Use the variable here
      entries = entries_str
    )
    response$content <- bundle_str
    return(response)
    
  } else {
    return(create_error_response(501, "NOT_IMPLEMENTED", "This server only supports calls for Patient, Observation or Procedure."))
  }
}

