BEGIN {
   Zeu = -1;
}

$0~/Euphotic depth/ && Zeu==-1 {
   Zeu = int($NF);
}

$0~/mean_ed/ {
   split($0,a,"=");
   PAR_Zml = a[2];
}

$0~/NPP/ {
   split($0,a,"=");
   NPP = a[2];
}

$0~/phi_mu_max/ {
   Phi_mu_max = $2;
}

$0~/prime/ {
  {if (npixels > 0) 
     PP = $NF*npixels;
   else
     PP = $NF;
  }
}

END {
   if (Zeu != -1) {
      printf "%s\t%d\t%f\t%f\t%f\t%f\n",
         station, Zeu, PAR_Zml, NPP, Phi_mu_max, PP;
   }
}
