$include "AgMIPSets.gms"

Parameter
   AgMIPData(Mod,Scen,r,v,i,t,u)
;

execute_load "AgMIPData3F.gdx", AgMIPData ;

set rfilter(r) / CAN, USA, BRA, OSA, FSU, EUR, MEN, SSA, CHN, IND, SEA, OAS, ANZ, NAM, OAM, AME, SAS, WLD, EUE / ;
*set vfilter(v) / popt, gdpt, cons, prod, area, land, yild, xprp, feed, calo, cali / ;
set vFilter(v) ; vFilter(v) = yes ;

set mapFilter(r,v) ; mapFilter(r,v)$(rfilter(r) and vfilter(v)) = yes ;

file csv / Diet.csv / ;
put csv ;
put "Model,Scenario,Region,Indicator,Sector,Unit,Year,Value" / ;
csv.pc=5 ;
csv.nd=9 ;

loop((mod,scen,r,v,i,t,u)$(mapFilter(r,v) and AgMIPData(Mod,Scen,r,v,i,t,u)),
   put mod.tl, scen.tl, r.tl, v.tl, i.tl, u.tl, t.val:4:0, AgMIPData(Mod,Scen,r,v,i,t,u) / ;
) ;
