################################################################################
##                                                                            ##  
##     Training and evaluating models (using the tidymodels framework)        ##  
##                                                                            ##  
################################################################################

# Learn more about tidymodels here: https://www.tidymodels.org/start/case-study/.

## -----------------------------------------------------------------------------
## Require packages
## -----------------------------------------------------------------------------

library(tidyverse)
library(tidymodels)
library(vip)
library(probably)

options(yardstick.event_first = TRUE) # treat the first level (1) as “positive” 

## -----------------------------------------------------------------------------
## Load and prepare preprocessed data
## -----------------------------------------------------------------------------

# Load data
df <- readRDS("Data_ready_for_workshop2.rds")

# Test and calibration data
df_test <- 
  df %>% 
  filter(split == "test")

df_cal <- 
  df %>% 
  filter(split == "calibration")

df_train <- 
  df %>% 
  filter(split == "train")

df_val <- 
  df %>% 
  filter(split == "validation")

# Make rsplit object (for train and validation data)
val_split <- 
  make_splits(
    list(analysis   = which(df$split == "train"),
         assessment = which(df$split == "validation")),
    data = df
  )

val_rs <- manual_rset(list(val_split), ids = "val")

# Recipe
the_recipe <- 
  recipe(event_1y ~ ., data = df_train) %>% 
  step_rm(id, split, date) 

prep(the_recipe) %>% juice() %>% glimpse

## -----------------------------------------------------------------------------
## Logistic regression - model training
## -----------------------------------------------------------------------------

# NB: no hyperparameters for logistic regression

# Setup model 
blr_mod <- 
  logistic_reg(
    mode = "classification",
    engine = "glm",
    penalty = NULL,
    mixture = NULL)

# Combine model and recipe into workflow (used for training phase)
blr_workflow <-
  workflow() %>% 
  add_model(blr_mod) %>% 
  add_recipe(the_recipe)

# Train model
blr_res <-
  blr_workflow %>% 
  fit_resamples(resamples = val_rs,
                control = control_resamples(save_pred = T))

# PR curve for validation set
blr_val_pr <- 
  blr_res %>% 
  collect_predictions() %>% 
  pr_curve(event_1y, .pred_1) %>% 
  mutate(model = "Logistic Regression")

autoplot(blr_val_pr)


## -----------------------------------------------------------------------------
## Elastic net - model training
## -----------------------------------------------------------------------------

# NB: two hyperparameters for elastic net (penalty and mixture)

# Setup model
el_mod <- 
  logistic_reg(
    mode = "classification",
    engine = "glmnet",
    penalty = tune(),
    mixture = tune()
  )

# Combine model and recipe into workflow (used for training phase)
el_workflow <-
  workflow() %>% 
  add_model(el_mod) %>% 
  add_recipe(the_recipe)

# Setup a manual grid for hyperparameter tuning (grid search)
el_grid <- expand_grid(
  penalty = 10^seq(-6, -2, length.out = 101),  
  mixture = seq(0, 1, length = 11)
)

# Tune model over grid (i.e. train model for each combo of penalty and mixture)
el_res <- 
  el_workflow %>% 
  tune_grid(resample = val_rs,
            grid = el_grid,
            control = control_grid(save_pred = TRUE),
            metrics = metric_set(pr_auc))

# Plot performance as function of tuning parameters
autoplot(el_res)

# Select best model, i.e. combo of penalty and mixture (based on PR AUC)
el_best <- el_res %>% select_best(metric = "pr_auc")

## -----------------------------------------------------------------------------
## Further models
## -----------------------------------------------------------------------------

# Using tidymodels you can easily fit several other models (fx random forest and 
# XGboost) by changing the argument to add_model() in the workflow specification

# Note, you can use 'workflowset' if you want to run many models. This
# allows for more elegant training and comparison of many models.

## -----------------------------------------------------------------------------
## Retrain models on combined training and validation set, using optimal 
## hyperparameters
## -----------------------------------------------------------------------------

# New splits 
df_split <- make_splits(
  list(
    analysis   = which(df$split %in% c("train", "validation")),
    assessment = which(df$split == "test")
  ),
  data = df
)


## Logistic regression ---------------------------------------------------------

# Train and evaluate model
blr_last_fit <- last_fit(blr_workflow, 
                         split = df_split,
                         metrics = metric_set(precision, roc_auc, pr_auc, brier_class),
                         add_validation_set = F)

# Performance metrics
blr_last_fit %>% collect_metrics()

# Most important features (vip depends on type of model. For the logistic model
# (a parametric model) we consider model coefficients (or something based on them))
blr_vars <- blr_last_fit %>% 
  pluck(".workflow", 1) %>%   
  extract_fit_parsnip() %>% 
  vip(num_features = 20, include_type = T)

blr_vars


## Elastic net -----------------------------------------------------------------

# Use hyperparameters determined earlier in workflow
el_final_workflow <- 
  el_workflow %>% 
  finalize_workflow(el_best)

# Train and evaluate model
el_last_fit <- 
  last_fit(
  el_final_workflow, 
  split = df_split,
  metrics = metric_set(precision, roc_auc, pr_auc, brier_class),
  add_validation_set = F
)

el_last_fit %>% collect_metrics()

# Most important features: 
el_vars <- 
  el_last_fit %>% 
  pluck(".workflow", 1) %>%   
  extract_fit_parsnip() %>% 
  vip(num_features = 20, include_type = T)

el_vars


## -----------------------------------------------------------------------------
## Summarise performance across models
## -----------------------------------------------------------------------------

# Brier, precision, PR AUC, ROC AUC
cbind(
  blr_last_fit %>% collect_metrics() %>% select(c(.metric, .estimate)) %>% rename(blr = .estimate),
  el_last_fit  %>% collect_metrics() %>% select(.estimate) %>% rename(el = .estimate)
)

results <- bind_rows(
  blr_last_fit %>% collect_metrics() %>% mutate(model = "Logistic"),
  el_last_fit  %>% collect_metrics() %>% mutate(model = "Elastic Net")
)

results %>%
  ggplot(aes(x = model, y = .estimate, fill = model)) +
  geom_col() +
  facet_wrap(~ .metric, scales = "free_y") +
  theme_minimal()

# PR curve
pr_curves <- bind_rows(
  blr_last_fit %>%
    collect_predictions() %>%
    pr_curve(event_1y, .pred_1) %>%
    mutate(model = "Logistic"),
  
  el_last_fit %>%
    collect_predictions() %>%
    pr_curve(event_1y, .pred_1) %>%
    mutate(model = "Elastic Net")
)

ggplot(pr_curves, aes(x = recall, y = precision, color = model)) +
  geom_path(linewidth = 1) +
  labs(title = "Precision-Recall Curve",
       color = "Model") +
  theme_minimal()

## -----------------------------------------------------------------------------
## Model calibration 
## -----------------------------------------------------------------------------

# Calibration is shown here for the elastic net model

# Predictions on test data
el_pred <- 
  el_last_fit %>% 
  collect_predictions() %>% 
  select(.row, el = .pred_1, event_1y)

# Predictions for the calibration data set
el_cal_pred <- 
  el_last_fit %>% 
  extract_workflow() %>% 
  predict(new_data = df_cal, type = "prob") %>% 
  select(el = .pred_1) %>% 
  bind_cols(event_1y = df_cal$event_1y)

# Platt calibration (logistic regression)
platt_model <- glm(
  I(event_1y == 1) ~ el,
  data = el_cal_pred,
  family = binomial())

summary(platt_model)

# Apply calibrations for calibration data (sanity check)
el_cal_pred <- 
  el_cal_pred %>%
  mutate(el_calibrated = predict(platt_model, type = "response"))

el_cal_pred %>%
  cal_plot_breaks(event_1y, el_calibrated, num_breaks = 20)

el_cal_pred %>% 
ggplot(aes(x = el, y = el_calibrated, col = event_1y)) + 
  geom_point()


# Apply calibrations for test data
el_pred <- 
  el_pred %>%
  mutate(el_calibrated = predict(platt_model, newdata = el_pred, type = "response"))

# Calibration plot using the "probably" package
p1 <- 
  el_pred %>% cal_plot_windowed(event_1y,  el, step_size = 0.02) +
  labs(title = "Calibration Plot - Uncalibrated Elastic Net")

p2 <- 
  el_pred %>% cal_plot_windowed(event_1y,  el_calibrated, step_size = 0.02) +
  labs(title = "Calibration Plot - Calibrated Elastic Net")

gridExtra::grid.arrange(p1, p2)


# Note: due to high class imbalance, too little data, and 
# the spread of predicted probabilities is quite small, the calibration plots 
# generated here are not that meaningful unfortunately. Do not put too much energy
# in trying to decipher the results from this. 
