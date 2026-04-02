* BCD cell netlists for LibreCell
* Contains HV inverter (VDDH domain) and standard inverter (VDD domain)

.subckt HV_INVX1 Y VDDH VSS A
M0 Y A VDDH VDDH pmos w=0.5u l=0.05u
+ ad=0p pd=0u as=0p ps=0u
M1 Y A VSS VSS nmos w=0.25u l=0.05u
+ ad=0p pd=0u as=0p ps=0u
.ends HV_INVX1

.subckt INVX1_BCD Y VDD VSS A
M0 Y A VDD VDD pmos w=0.5u l=0.05u
+ ad=0p pd=0u as=0p ps=0u
M1 Y A VSS VSS nmos w=0.25u l=0.05u
+ ad=0p pd=0u as=0p ps=0u
.ends INVX1_BCD
