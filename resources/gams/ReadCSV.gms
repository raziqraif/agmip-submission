$include "AgMIPSets.gms"

Parameter
   AgMIPData(Mod,Scen,r,v,i,t,u)
;

$offlisting
$offdigit
Parameter AgMIPData(Mod,Scen,r,v,i,t,u) /
$ondelim
$include "AIM/AIM_DIET_ALL_18FEB202115MAR2021.csv"
$include "CAPRI/AgMip_CAPRI_diet_results_Feb1815MAR2021.csv"
$include "FARM/FARM4_AgMIP_diet_038a15MAR2021.csv"
$include "GCAM/GCAM_DIET_ALL_17Dec202015FEB2021.csv"
$include "GLOBIOM/output_GLOBIOM_AgMIP3_12mar202115MAR2021.csv"
$include "IMAGE/IMAGE_DIET_ALL_12DEC202007DEC2020.csv"
$include "IMPACT/IMPACT_DIET_ALL_09FEB202115FEB2021.csv"
$include "MAGNET/DietAgMIP_MAGNET_2020-12-1111DEC2020.csv"
$include "MAgPIE/MAgPIE_agmip_ssp_2p6_preliminary_20-01-2212MAY2020.csv"
$include "MAgPIE/MAgPIE_agmip_ssp123_diet_scenarios_20-11-2707DEC2020.csv"
$offdelim
/ ;
$onlisting

execute_unload "AgMIPData3F.gdx", AgMIPData ;
