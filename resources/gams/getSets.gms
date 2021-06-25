$include "AgMIPSets.gms"

Parameter
   AgMIPData(Mod,Scen,r,v,i,t,u)
;

execute_load "AgMIPData3F.gdx", AgMIPData ;

Parameters
   ScenCount(mod,scen)
   RegCount(mod,r)
   VarCount(mod,v)
   SecCount(mod,i)
   YearCount(mod,t)
   UnitCount(mod,u)
;

*  Scenarios
ScenCount(mod,Scen) = sum((r,v,i,t,u)$agmipdata(mod,scen,r,v,i,t,u), 1) ;

file fscen / Scen.csv / ;
put fscen ;
put "Model,Scenario,Flag" / ;
fscen.pc=5 ;
loop((mod,Scen)$ScenCount(mod,Scen),
   put mod.tl, Scen.tl, 1:0:0 / ;
) ;

*  Regions
RegCount(mod,R) = sum((Scen,v,i,t,u)$agmipdata(mod,scen,r,v,i,t,u), 1) ;

file freg / Reg.csv / ;
put freg ;
put "Model,Region,Flag" / ;
freg.pc=5 ;
loop((mod,r)$RegCount(mod,R),
   put mod.tl, R.tl, 1:0:0 / ;
) ;

*  Indicators
VarCount(mod,v) = sum((Scen,r,i,t,u)$agmipdata(mod,scen,r,v,i,t,u), 1) ;

file fvar / var.csv / ;
put fvar ;
put "Model,Variable,Flag" / ;
fvar.pc=5 ;
loop((mod,v)$VarCount(mod,v),
   put mod.tl, v.tl, 1:0:0 / ;
) ;

*  Sectors
SecCount(mod,i) = sum((Scen,r,v,t,u)$agmipdata(mod,scen,r,v,i,t,u), 1) ;

file fsec / item.csv / ;
put fsec ;
put "Model,Item,Flag" / ;
fsec.pc=5 ;
loop((mod,i)$SecCount(mod,i),
   put mod.tl, i.tl, 1:0:0 / ;
) ;

*  Years
YearCount(mod,t) = sum((Scen,r,v,i,u)$agmipdata(mod,scen,r,v,i,t,u), 1) ;

file fyear / year.csv / ;
put fyear ;
put "Model,Year,Flag" / ;
fyear.pc=5 ;
loop((mod,t)$YearCount(mod,t),
   put mod.tl, t.val:4:0, 1:0:0 / ;
) ;

*  Units
UnitCount(mod,u) = sum((Scen,r,v,i,t)$agmipdata(mod,scen,r,v,i,t,u), 1) ;

file funit / unit.csv / ;
put funit ;
put "Model,Unit,Flag" / ;
funit.pc=5 ;
loop((mod,u)$UnitCount(mod,u),
   put mod.tl, u.tl, 1:0:0 / ;
) ;
