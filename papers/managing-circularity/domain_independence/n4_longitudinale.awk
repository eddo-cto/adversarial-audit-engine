BEGIN{FS="\t"; m["Jan"]=1;m["Feb"]=2;m["Mar"]=3;m["Apr"]=4;m["May"]=5;m["Jun"]=6;m["Jul"]=7;m["Aug"]=8;m["Sep"]=9;m["Oct"]=10;m["Nov"]=11;m["Dec"]=12}
function dk(s,  a,n){ if(s=="-"||s=="")return 0; n=split(s,a," "); if(n<3)return 0; if(!(a[1] in m))return 0; sub(/,/,"",a[2]); return a[3]*10000+m[a[1]]*100+a[2] }
function bk(s){ if(s=="Uncertain significance")return "V"; if(s=="Pathogenic"||s=="Likely pathogenic"||s=="Benign"||s=="Likely benign"||s=="Pathogenic/Likely pathogenic"||s=="Benign/Likely benign")return "D"; return "O" }
function proc(  i,minv,startb,i1,i2,i3,d1,d2,d3,cD,cV,fin,cat,nb){
 if(cnt<3)return
 minv=1e18; for(i=1;i<=cnt;i++){if(KD[i]<minv){minv=KD[i];startb=KB[i]}}
 if(startb!="V")return
 nvar++
 i1=0;d1=-1;i2=0;d2=-1;i3=0;d3=-1
 for(i=1;i<=cnt;i++){ if(KD[i]>d1){d3=d2;i3=i2;d2=d1;i2=i1;d1=KD[i];i1=i} else if(KD[i]>d2){d3=d2;i3=i2;d2=KD[i];i2=i} else if(KD[i]>d3){d3=KD[i];i3=i} }
 cD=0;cV=0
 if(KB[i1]=="D")cD++;else if(KB[i1]=="V")cV++
 if(KB[i2]=="D")cD++;else if(KB[i2]=="V")cV++
 if(KB[i3]=="D")cD++;else if(KB[i3]=="V")cV++
 if(cD>=2)fin="D";else if(cV>=2)fin="V";else fin=KB[i1]
 resolved=(fin=="D"); cat=(hasx?"expert":"peer")
 tot[cat]++; if(resolved)res[cat]++
 if(cat=="peer"){ nb=(nsub<=4?"3-4":(nsub<=9?"5-9":"10+")); pn[nb]++
   if(resolved){pnr[nb]++; yr=int(d1/10000)-int(minv/10000); ysum+=yr; ycnt++} }
}
{ vid=$1
  if(vid!=cur){ if(cur!="")proc(); cur=vid; cnt=0; hasx=0; nsub=0; delete SB }
  d=dk($3); if(d>0){cnt++; KD[cnt]=d; KB[cnt]=bk($2)}
  if($4=="reviewed by expert panel"||$4=="practice guideline")hasx=1
  if(!($5 in SB)){SB[$5]=1;nsub++}
  nrows++
}
END{ if(cur!="")proc()
 printf "righe: %d | varianti nate-VUS (>=3 sub datate): %d\n",nrows,nvar
 printf "  DEF con EXPERT PANEL nel percorso : %d/%d = %.1f%%\n",res["expert"],tot["expert"],(tot["expert"]?100*res["expert"]/tot["expert"]:0)
 printf "  DEF PEER-ONLY (mai expert panel)  : %d/%d = %.1f%%\n",res["peer"],tot["peer"],(tot["peer"]?100*res["peer"]/tot["peer"]:0)
 print  "  peer-only, dose-risposta (n. sottomettitori distinti):"
 split("3-4 5-9 10+",K," ")
 for(k=1;k<=3;k++){b=K[k]; printf "     %-4s: %d/%d = %.1f%%\n",b,pnr[b],pn[b],(pn[b]?100*pnr[b]/pn[b]:0)}
 if(ycnt)printf "  tempo medio a risoluzione (peer-only): %.1f anni (n=%d)\n",ysum/ycnt,ycnt
}
