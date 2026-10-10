## ECON 472
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-August_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-January_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-April_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-December_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-February_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-June_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-July_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-March_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-May_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-November_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-October_F1.RData")
load("C:/Users/lincy/Downloads/lfs-71M0001XCB-E-2015-September_F1.RData")
install.packages("dplyr")
library(dplyr)
install.packages("skimr")
library(skimr)
SEX <- ifelse(table$SEX == 1, 0,
              ifelse(table$SEX == 2, 1, table$SEX))
MAR <- ifelse(table$MARSTAT == 1, 1,
              ifelse(table$MARSTAT == 3, 0,
                     ifelse(table$MARSTAT == 2, 1,
                            ifelse(table$MARSTAT == 4, 0,
                                   ifelse(table$MARSTAT == 5, 0,
                                          ifelse(table$MARSTAT == 6, 0,
                     table$MARSTAT))))))
YoungAge_0_5 <- ifelse(table$AGYOWNKN %in% c(1, 2), 1, 0)
YoungAge_6_17 <- ifelse(table$AGYOWNKN %in% c(3, 5), 1, 0)
YoungAge_18_24 <- ifelse(table$AGYOWNKN == 6, 1, 0)
LFP <- ifelse(table$LFSSTAT == 1 & table$NAICS_18 == 11, 1, 0
              )
skim(SEX)
skim(MAR)
skim(LFP)
skim(YoungAge_0_5)
skim(YoungAge_6_17)
skim(YoungAge_18_24) # Missing var

model_stage1 <- glm(LFP ~ SEX, data = table, family = binomial(link = "logit"))
summary(model_stage1)
model_stage2 <- glm(LFP ~ SEX * YoungAge_0_5 + SEX * MAR + SEX * YoungAge_3_5
                    + SEX * YoungAge_6_12,+ SEX * YoungAge_13_17 + SEX * YoungAge_18_24,
                    data = table, family = binomial(link = "logit"))

# Summary of the model
summary(model_stage2) # Invalid
# Weight all factor
table$LFP <- ifelse(table$LFSSTAT == 1 & table$NAICS_18 == 11, 1, 0)
weights <- ifelse(table$LFP == 1,
                   1,
                  sum(table$LFP == 1) / sum(table$LFP == 0))
length(weights)
sum(is.na(table$LFP))  # Count missing values in LFP
sum(is.na(weights))    # Count missing values in weights

model_stage2_weighted <- glm(LFP ~ SEX * (YoungAge_0_5 + MAR + YoungAge_6_17),
                            data = table, family = binomial(link = "logit"),
                            weights = weights)
