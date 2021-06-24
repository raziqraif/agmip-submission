sets
   tt / 1995*2100 /
   t(tt) /
      1995
      2000
      2005
      2010
      2011
      2012
      2015
      2020
      2025
      2030
      2035
      2040
      2045
      2050
      2055
      2060
      2070
      2080
      2090
      2100
   /
   scen "Scenarios" /

*     Core scenarios

      "SSP1_NoMt_NoCC"
      "SSP2_NoMt_NoCC"
      "SSP3_NoMt_NoCC"
      "SSP1_NoMt_CC26"
      "SSP2_NoMt_CC26"
      "SSP3_NoMt_CC26"
      "SSP1_NoMt_CC85"
      "SSP2_NoMt_CC85"
      "SSP3_NoMt_CC85"

      "SSP1_2p6_NoCC"
      "SSP2_2p6_NoCC"
      "SSP3_2p6_NoCC"
      "SSP1_2p6_CC26"
      "SSP2_2p6_CC26"
      "SSP3_2p6_CC26"
      "SSP1_2p6_CC26_noagm"
      "SSP2_2p6_CC26_noagm"
      "SSP3_2p6_CC26_noagm"

*     Deep decarbonization scenarios

      "SSP1_1p9_CC26"
      "SSP2_1p9_CC26"
      "SSP3_1p9_CC26"
      "SSP1_1p9_CC26_noagm"
      "SSP2_1p9_CC26_noagm"
      "SSP3_1p9_CC26_noagm"

*     Mitigation scenarios (Globiom)
      "SSP1_Mit_Full"
      "SSP1_Mit_wAff"
      "SSP1_Mit_wBio"
      "SSP1_Mit_wNonCO2"
      "SSP2_Mit_Full"
      "SSP2_Mit_wAff"
      "SSP2_Mit_wBio"
      "SSP2_Mit_wNonCO2"
      "SSP2_Mit_woAff"
      "SSP2_Mit_woBio"
      "SSP2_Mit_woNonCO2"
      "SSP3_Mit_Full"
      "SSP3_Mit_wAff"
      "SSP3_Mit_wBio"
      "SSP3_Mit_wNonCO2"

*     Extreme event scenarios

      "SSP2_NoMt_CC26_Y30MIN"
      "SSP2_NoMt_CC26_Y30MAX"
      "SSP2_NoMt_CC26_Y85MIN"
      "SSP2_NoMt_CC26_Y85MAX"
      "SSP2_NoMt_CC85_Y30MIN"
      "SSP2_NoMt_CC85_Y30MAX"
      "SSP2_NoMt_CC85_Y85MIN"
      "SSP2_NoMt_CC85_Y85MAX"

*     Diet change scenarios

      "SSP2_NoMt_NoCC_FlexA_WLD"
      "SSP2_NoMt_NoCC_FlexA_USA"
      "SSP2_NoMt_NoCC_FlexA_EUR"
      "SSP2_NoMt_NoCC_FlexA_CHN"
      "SSP2_NoMt_NoCC_FlexA_LAM"
      "SSP2_NoMt_NoCC_FlexA_DEV"
      "SSP2_NoMt_NoCC_HalfRD_DEV"
      "SSP2_NoMt_NoCC_HalfRDoM_DEV"

*     IMAGE
      "SSP2_NoMt_NoCC_HalfRDoM_DEV_noe"
      "SSP2_NoMt_NoCC_HalfRD_DEV_noe"

*     FARM
      "SSP2_Baseline"

*     IMPACT
      "SSP2_NoMt_NoCC_FlexA_WLD_2500"

*     Capri
      "SSP2_NoMt_NoCC_FlexA_WLD_Fwaste"
      "SSP2_NoMt_NoCC_FlexA_WLD_2500_Fwaste"
  /

   mod "Models" /
      "AIM"
      "FARM"
      "GLOBIOM"
      "IMAGE"
      "IMPACT"
      "MAGNET"
      "MAgPIE"
      "CAPRI"
      "GCAM"
      "GAPS"
   /

   r  "Regions" /

*     Core regions

      "CAN"     "Canada"
      "USA"     "United States of America"
      "BRA"     "Brazil"
      "OSA"     "Other South, Central America & Caribbean (incl. Mexico)"
      "FSU"     "Former Soviet Union (European and Asian)"
      "EUR"     "Europe (excl. Turkey)"
      "MEN"     "Middle-East / North Africa (incl. Turkey)"
      "SSA"     "Sub-Saharan Africa"
      "CHN"     "China (incl Hong-Kong, Macao)"
      "IND"     "India"
      "SEA"     "South-East Asia (incl. Japan, Taiwan)"
      "OAS"     "Other Asia (incl. Other Oceania)"
      "ANZ"     "Australia/New Zealand"

*     Aggregate regions

      "NAM"     "North America (Canada & USA)"
      "OAM"     "Other Americas (South, Central & Caribbean)"
      "AME"     "Africa & Middle East"
      "SAS"     "Southern Asia"

*     World
      "WLD"     "World"

*     Optional
      "EUE"     "EU28 Members States"

*     Non-protocol regions

*     GLOBIOM
      "ROW"

*     MAgPIE
      "JPN"
      "REF"
      "CAZ"
      "CHA"
      "LAM"
      "MEA"
      "NEU"
      "World"

*     CAPRI
      "AUT"
      "BEL"
      "BGR"
      "CYP"
      "CZE"
      "DEU"
      "DNK"
      "ESP"
      "EST"
      "FIN"
      "FRA"
      "GBR"
      "GRC"
      "HRV"
      "HUN"
      "IRL"
      "ITA"
      "LTU"
      "LVA"
      "MLT"
      "NLD"
      "POL"
      "PRT"
      "ROU"
      "SVK"
      "SVN"
      "SWE"

   /
   v  "Indicator" /
      "POPT"     "Total population--million"
      "GDPT"     "Total GDP (MER)--bn USD 2005 MER"
      "XPRP"     "Real producer price/input price--USD/t"
      "XPRX"     "Real export price--USD/t"
      "AREA"     "Area harvested--1000 ha"
      "ARRF"     "Area harvested - rainfed--1000 ha"
      "ARIR"     "Area harvested - irrigated--1000 ha"
      "LAND"     "Land cover--1000 ha"
      "YILD"     "Crop yield--dm t/ha, fm t/ha"
      "YIRF"     "Crop yield - rainfed--dm t/ha, fm t/ha"
      "YIIR"     "Crop yield - irrigated--dm t/ha, fm t/ha"
      "YEXO"     "Exogenous crop yield--dm t/ha, fm t/ha"
      "YECC"     "Climate change shifter on crop yield--%"
      "LYLD"     "Livestock yield (endogenous)--kg prt/ha"
      "LYXO"     "Exogenous livestock yield trend--kg prt/ha"
      "FEEF"     "Feed conversion efficiency (endogenous)--kg prt/kg prt"
      "FEXO"     "Feed conversion efficiency trend--kg prt/kg prt"
      "FOOD"     "Food use--1000 t"
      "FEED"     "Feed use--1000 t"
*     "FEED"     "Feed use--1000 t prt"
      "OTHU"     "Other use--1000 t"
      "IMPO"     "Imports--1000 t"
      "EXPO"     "Exports--1000 t"
      "FRTN"     "Fertiliser N--1000 t"
      "WATR"     "Water for irrigation--km3"
      "CALO"     "p.c. calory availability--kcal/cap/d"
      "CALI"     "p.c. calory intake--kcal/cap/d"
      "PROD"     "Production--1000 t"
      "CONS"     "Domestic use--1000 t"
      "NETT"     "Net trade--1000 t"
      "FRUM"     "Feed use ruminant meat--1000 t"
*     "FRUM"     "Feed use ruminant meat--1000 t prt"
      "FNRM"     "Feed use non-ruminant--1000 t"
*     "FNRM"     "Feed use non-ruminant--1000 t prt"
      "FDRY"     "Feed use dairy--1000 t"
*     "FDRY"     "Feed use dairy--1000 t prt"
      "FFSH"     "Feed fish sector--1000 t"
*     "FFSH"     "Feed fish sector--1000 t prt"
      "EMIS"     "Total GHG emissions--MtCO2e"
      "ECO2"     "Total CO2 emissions--MtCO2e"
      "ECH4"     "Total CH4 emissions--MtCO2e"
      "EN2O"     "Total N2O emissions--MtCO2e"
      "CTAX"     "Carbon tax level--USD/tCO2e"
      "TPRD"     "Technical mitigation options - Production--1000 t"
      "TGHG"     "Technical mitigation options - Emissions--MtCO2e"
      "TCO2"     "Technical mitigation options - CO2--MtCO2e"
      "TCH4"     "Technical mitigation options - CH4--MtCO2e"
      "TN2O"     "Technical mitigation options - N2O--MtCO2e"

*     Additional AIM
      "XPRR"

*     Additional FARM
      "XPRP_deflated"
      "PROD_tons"
      "YILD_tons"
      "PcalFoodTotal"
      "PcalDomSupplyPrimary"
      "PcalProdPrimary"
      "areaFoodCrops"
      "foodIncomeShare"

*     MAgPIE
      "YILD_endoTC"

*     MAGNET
      "PROT"
      "VIPM"
      "GDPVal"
      "NQT"
      "GCH4"
      "GN2O"
   /
   i  "Sector/items" /
*     Core sectors
      "RIC"     "Rice (paddy equivalent)"
      "WHT"     "Wheat"
      "CGR"     "Other cereal grains"
      "OSD"     "Oilseeds (raw equivalent)"
      "SGC"     "Sugar crops (raw equivalent)"
      "VFN"     "Vegetables, fruits, nuts (incl. roots and tubers)"
      "PFB"     "Plant based fibres"
      "ECP"     "Energy crops"
      "OCR"     "Other crops"
      "RUM"     "Ruminant meats"
      "NRM"     "Non ruminant meats"
      "DRY"     "Dairy (raw milk equivalent)"
      "OAP"     "Other animal products (wool, honey)"
      "GRS"     "Grass"
      "OFD"     "Other feed products"
      "FSH"     "Fish"
      "FOR"     "Forestry products"

*     Sectors subcategories (same variables as parents)

      "VFN|VEG"     "Vegetables"
      "VFN|FRU"     "Fruits"
      "VFN|NUT"     "Nuts"
      "NRM|PRK"     "Pork meat"
      "NRM|PTM"     "Poultry meat"
      "NRM|EGG"     "Poultry eggs"
      "NRM|ONR"     "Other non-ruminant"

*     Sectors aggregates
      "CRP"     "All crops"
      "LSP"     "Livestock products"
      "AGR"     "All agricultural products"
      "TOT"     "Total (full economy, population, GDP, calories)"

*     Land items

*     "CRP"     "Cropland (including energy crops)"
*     "GRS"     "Grassland"
      "ONV"     "Other natural land"
*     "FOR"     "Managed and primary forest"
      "NLD"     "Non arable land (desert, built-up areas…)"

*     LAND aggregates/subitems
*     "AGR"     "Cropland + grassland"
*     "ECP"     "Energy crops (included in cropland)"

*  Production factors and intermediates
      "LAB"     "Labor"
      "CAP"     "Capital"
      "FRT"     "Fertiliser"
      "OIL"     "Fossil fuel"

*  GHG emissions sources
      "ENT"     "Enteric Fermentation"
      "MMG"     "Manure Management"
      "RCC"     "Rice Cultivation"
      "SFR"     "Synthetic Fertilizers"
      "MAS"     "Manure applied to Soils"
      "MGR"     "Manure left on Pasture"
      "CRS"     "Crop Residues"
      "ORS"     "Cultivation of Organic Soils"
      "BSV"     "Burning - Savanna"
      "BCR"     "Burning - Crop Residues"

$ontext
*  GHG mitigation technologies
      "LAD"     "Livestock anaerobic digesters"
      "LFS"     "Livestock feed supplements"
      "LOT"     "Livestock other"
      "CFT"     "Crop improved fertilization"
      "CMG"     "Improved cropping management"
      "RMG"     "Crop improved rice cultivation"
      "COT"     "Crop other"
$offtext

*  >>>> End of protocol items <<<<

*     AIM
      "CR5"
      "FRS"
      "PAS"

*     2/3 models (GLOBIOM,IMPACT,CAPRI)
      "VEG"
      "FRU"
      "NUT"
      "PRK"
      "PTM"
      "EGG"

*     CAPRI
      "BEF"
      "SGM"
      "POM"

*     GCAM
      "NA"

*     MAgPIE
      "URB"

*     GAPS
      "OCT"
   /

   u "Units" /

*     Core units

      "million"
      "bn USD 2005 MER"
      "USD/t"
      "1000 ha"
      "fm t/ha"
      "dm t/ha"
      "%"
      "kg prt/ha"
      "kg prt/kg prt"
      "1000 t"
      "1000 t prt"
      "km3"
      "kcal/cap/d"
      "MtCO2e"
      "USD/tCO2e"

*     Close to core

      "t/ha"

*     AIM
      "bn USD 2005"

*     FARM
      "Tcal"
      "bn USD 2011 MER"
      "PCAL"
      "Mha"
      "USD/tCO2"
      "USD/Gcal"
      "Gcal/ha"
      "fraction"

*     GLOBIOM
      "kg prt/t dm"
      "1000 m3"

*     MAgPIE
      "1000 t dm"
      "USD/USD"
      "%/yr"
      "1"
      "MtCH4"
      "MtCO2"
      "MtN2O"

*     IMPACT

      "%/year"
      "kcal/cap/day"
      "usd per t CO2"
      "bn USD 2005 PPP"

*     CAPRI
      "Million cap"
      "EUR2010/cap"
      "EUR2010/t dm"
      "EUR2010/t fm"
      "t dm/ha"
      "1000 t fm"
      "t fm/ha"

*     MAGNET
      "mn USD"
      "mn pers"
      "USD/ha"
      "index (2011 = 100)"
      "Paasche index"
      "bn USD 2007 MER"
      "g/cap/d"
      "bn USD MER"
      "CAL"

*     IMAGE
      "bn USD 2011"
      "Index (2015 = 1)"
   /
;
