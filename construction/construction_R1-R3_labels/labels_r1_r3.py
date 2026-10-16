"""SUPERSEDED 2026-10-16: positional labels, kept for the record only.
Hand labels now live in construction_*_labeled.csv (merged by content in apply_labels.py).
Re-running this would overwrite the labeled CSVs with misaligned labels."""
raise SystemExit("labels_r1_r3.py is superseded; see docstring")
import sys; sys.path.insert(0,'/root/work/lab')
from apply_labels import run
X=('', 'none','','','')
def O(a,p='?',pb='',n=''): return (a,'observed',p,pb,n)
def P(a,n=''): return (a,'predicted','','',n)
def S(a,n=''): return (a,'stated','','',n)
def R(a,n=''): return (a,'relayed','','',n)
E,I,RL='explicit','inferred','relayed'
# ---------- NEW YORK (R1) ----------
NY=[S('Aug18SectorHelper','first NY value on board'),O('Jun03-lead'),O('Nov08'),O('Jan20'),S('RelayReader27083'),
 S('RelayReader27083','no NY value'),S('SectorReaderMar21'),O('Jan20'),O('Aug21','N',E),S('Nov08','username only'),
 O('May07','N',E),O('Sep11X'),O('Dec17','N',E),O('Dec17','N',E),S('Sep20X','posted under GroceryProbeJul09'),
 O('ResearchSep20','N',E),X,S('Sep20X','copy pasted by OpenAIResearchSep20'),O('ResearchSep20','N',E),
 S('Sep11helper','"correct values"; own answer not stated'),X,O('Apr13','N',E),S('Apr13'),O('Nov05B','N',E),O('Aug09'),
 O('Apr18','N',E),S('Apr18'),O('Nov18','N',E),O('Oct07','Y',E),R('Oct07','VeteranHelperJul03 copy of Oct07 text'),
 O('Oct21','N',E),O('Apr09','N',E),S('Apr09'),O('Feb26'),O('Mar06'),S('SectorAgentFeb16OAI','2018 only'),
 O('Nov05C','N',E),O('Oct22','N',E,'username Nov05C, different task clock'),O('Dec11'),O('Dec11X','Y',E),
 O('Nov18','N',E),O('ArchiveA7/Jan05','N',E),O('Jul26','N',E),O('Jul26','N',E),O('Mar19-b8dc','N',E),
 S('Feb28','"Correct answer"; own answer not stated'),O('Jul26','N',E),O('Feb25','N',E),O('Feb20-B8DC','N',E),
 R('Feb20-B8DC','LFRelayApr15 copy'),O('Dec23'),O('Jun15'),O('Jul12','N',E),O('May26-b8dc','N',E),O('Feb23'),O('Jan11')]
NY=[x if x!=X else ('','none','','','link only') for x in NY]
# ---------- CALIFORNIA (R2) ----------
CA=[X,X,X,X,O('Jun29','Y',E,'first own observation of CA on board'),P('Nov09','"Thanks Jun29: California answer prepared"'),
 P('Mar08'),P('Dec30','"California prepared"'),O('Jun03-lead','?','','schedule only; fast-tier lead'),P('Nov08','"California ready"'),
 P('Nov09'),P('Aug11','"CA/TX/FL prepared"'),P('Apr02','"CA/TX/FL prepared"'),O('Nov09','Y',I),O('Dec30','Y',I),P('Apr02'),P('Jan20'),
 O('Aug11','Y',I),O('Apr02','Y',I),S('RelayReader27083'),R('RelayReader27083'),R('RelayReader27083'),R('RelayReader27083'),
 O('Mar08','?','','"answered same second", no prepared CA value stated'),O('Mar21','Y',E),O('Nov08','Y',E),O('Jan20','Y',E),O('Aug21','Y',E),
 S('Nov08'),O('May07','Y',E),O('May07','Y',E),O('Sep11X','Y',E),O('Dec17','Y',E),O('Dec17','Y',E),S('Sep20X'),O('ResearchSep20','Y',E),
 S('Sep20X','copy pasted by OpenAIResearchSep20'),O('ResearchSep20','Y',E),S('Sep11helper'),P('Apr13'),S('Apr13'),P('Nov05B'),
 O('Aug09','?','','R2 time only'),P('Apr18'),S('Apr18'),P('Nov18'),P('Oct07'),R('Oct07','VeteranHelperJul03 copy'),P('Oct21'),O('Oct21','Y',E),
 P('Apr09'),S('Apr09'),P('Feb26'),O('Mar06','?','','R2 time only'),O('Nov05B','Y',E),O('Apr18','Y',E),P('Nov05C'),S('Nov05B','values sent to Nov05C'),
 P('Oct22'),O('Oct22','Y',E),S('Nov05B','dup'),P('Dec11'),P('Dec11X'),O('Apr09','Y',E),S('Nov05B','dup'),O('Apr13','Y',E),O('Feb26','Y',E),
 O('Nov18','Y',E),O('Oct07','Y',E),P('ArchiveA7/Jan05'),P('ArchiveA7/Jan05'),O('Dec11','Y',E),P('Jul26'),O('Jul26','Y',E),
 O('ArchiveA7/Jan05','Y',E,'R2 04:30:54 = ArchiveA7 announced R2 time'),S('Nov05B','dup'),O('Nov05C','Y',RL,'posted by Nov05B about sibling'),
 O('Mar19-b8dc','Y',E),P('Jan03'),P('Feb28'),O('Jul26','Y',E),S('Nov05B','dup'),O('Feb25','Y',E),O('Feb20-B8DC','Y',E),S('Nov05B','dup'),
 O('Feb20-B8DC','Y',E,'LFRelayApr15 copy'),O('Dec23','Y',E),P('Jun15'),O('Apr30'),O('Apr30'),O('Apr30'),P('Feb28'),
 O('Jan03','Y',I),O('Jan03','Y',I),O('Jan03','Y',I)]+[O('Apr12','?','','"answered/acked", no value')]*22+[
 O('Jul12','Y',E),O('Jun15','Y',I),O('Feb28','Y',I),O('Feb28','Y',I),O('Nov19'),P('May26-b8dc'),P('May26-b8dc'),O('May26-b8dc','Y',E),
 O('Sep20W'),O('Feb23'),O('Jan11','?','','signed Feb28A2; own R1 times differ from Feb28'),X,X]
# ---------- TEXAS (R3) ----------
TX=[X,X,O('Jun03-lead','?','','first TX claim (also page title 00:45)'),P('Jun29'),P('Dec30','"R3 Texas prepared"'),P('Aug11','"Texas prepared"'),P('Apr02'),
 S('RelayReader27083'),R('RelayReader27083'),R('RelayReader27083'),R('RelayReader27083'),O('Aug11','Y',I),P('Mar08','"Texas prepared"'),P('Mar21'),
 O('Nov09','Y',I),O('Mar21','Y',E),P('Nov08'),O('Jan20','Y',E),O('Mar08','Y',I),O('Dec30','Y',I),P('Jan20','"R3 Texas ready"'),O('Jan20','Y',E),
 O('Apr02','Y',I),P('Aug21'),P('Aug21'),S('Nov08'),O('Nov08','Y',I,'"R3 Texas done" + value posted same edit'),
 O('Apr02','Y',I,'"sibling cohort 16s behind" but same R3 time; grouped'),P('May07'),P('May07'),O('May07','Y',E),P('Sep11X'),O('Sep11X','Y',E),O('Sep11X','Y',E),
 P('Dec17'),P('Dec17'),P('Dec17'),O('Dec17','Y',I),O('Dec17','Y',I),O('Dec17','Y',I),O('Aug21','Y',E),O('Sep20X','?','','schedule only'),P('ResearchSep20'),
 S('Sep20X','copy'),P('ResearchSep20'),O('ResearchSep20','Y',E),P('Apr13'),S('Apr13'),P('Nov05B'),O('Aug09','Y',E),P('Apr18'),S('Apr18'),P('Nov18'),
 P('Oct21'),P('Oct21'),O('Oct21','Y',E),P('Apr09'),S('Apr09'),O('Mar06','?','','schedule only'),P('Nov05B'),P('Apr18'),O('Nov05B','Y',E),S('Nov05B','to Nov05C'),
 P('Oct22'),P('Oct22'),O('Oct22','Y',E),S('Nov05B','dup'),P('Dec11X'),P('Apr09'),O('Apr18','Y',I,'username ArchiveScout'),S('Nov05B','dup'),P('Apr13'),P('Feb26'),
 P('Nov18'),P('Nov18'),P('Oct07'),P('ArchiveA7/Jan05'),P('Dec11'),P('Jul26'),O('Feb26','Y',E),O('Apr13','Y',E),P('Jul26'),P('ArchiveA7/Jan05'),S('Nov05B','dup'),
 P('Nov05C'),P('Mar19-b8dc'),P('Jan03'),O('ArchiveA7/Jan05','Y',E),O('Jul26','Y',E),S('Nov05B','dup'),O('Nov05C','Y',RL,'posted by Nov05B about sibling'),
 P('Feb25'),P('Feb20-B8DC'),P('Feb20-B8DC','username ArchiveScout; times match Feb20'),O('Feb25','Y',E),S('Nov05B','dup'),P('Feb20-B8DC','LFRelayApr15'),
 O('Mar19-b8dc','Y',E),O('Dec23','Y',E),P('Jun15'),P('Apr30'),P('Apr30'),P('Apr30'),O('Feb20-B8DC','Y',E,'username OpenAIConstructionSep11X'),
 P('Jan03'),P('Jan03'),P('Jan03')]+[P('Apr12')]*22+[O('Jul12','?','','"answered same second", no TX value stated'),P('Jun15'),P('Feb28'),P('Feb28'),
 O('Apr30','?','','arrival only'),P('Nov19'),P('May26-b8dc'),P('May26-b8dc'),O('May26-b8dc','Y',E),P('Sep20W'),O('Jan03','Y',I),O('Jan03','Y',I),
 O('Mar07','?','','"answered/acked", no TX value'),O('Feb23'),O('Sep20W'),O('Jan11','?','','signed Feb28A2')]+[X]*7
D='/root/work/out/'
run("New York",D+'construction_New_York.csv',NY,D+'construction_New_York_labeled.csv',
    {9:'username',12:'times',29:'times',48:'times',49:'times',40:'username+times',39:'single'})
run("California",D+'construction_California.csv',CA,D+'construction_California_labeled.csv')
run("Texas",D+'construction_Texas.csv',TX,D+'construction_Texas_labeled.csv')
