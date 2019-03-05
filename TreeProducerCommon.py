import re, math
from math import sqrt, sin, cos, pi
import numpy as num 
import ROOT
from ROOT import TTree, TH1D, TH2D, TLorentzVector, TVector3
from CorrectionTools.RecoilCorrectionTool import hasBit
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection


var_dict = {
  'Electron_mvaFall17Iso':      'Electron_mvaFall17Iso',
  'Electron_mvaFall17Iso_WPL':  'Electron_mvaFall17Iso_WPL',
  'Electron_mvaFall17Iso_WP80': 'Electron_mvaFall17Iso_WP80',
  'Electron_mvaFall17Iso_WP90': 'Electron_mvaFall17Iso_WP90',
}

def setYear(year):
  """Help function to change the name of some variables that depend on the year."""
  if year==2018 or year==2016:
    print "setYear: setting var_dict to year %s"%(year)
    var_dict['Electron_mvaFall17Iso']      = 'Electron_mvaFall17V2Iso'
    var_dict['Electron_mvaFall17Iso_WPL']  = 'Electron_mvaFall17V2Iso_WPL'
    var_dict['Electron_mvaFall17Iso_WP80'] = 'Electron_mvaFall17V2Iso_WP80'
    var_dict['Electron_mvaFall17Iso_WP90'] = 'Electron_mvaFall17V2Iso_WP90'
  
def getvar(obj,var):
  """Help function to get some variable's real name from the dictionary."""
  return getattr(obj,var_dict[var])
  
def getVLooseTauIso(year):
  """Return a method to check whether event passes the VLoose working
  point of all available tau IDs. (For tau ID measurement.)"""
  return lambda e,i: ord(e.Tau_idMVAoldDM[i])>0 or ord(e.Tau_idMVAnewDM2017v2[i])>0 or ord(e.Tau_idMVAoldDM2017v1[i])>0 or ord(e.Tau_idMVAoldDM2017v2[i])>0
  
def getMETFilters(year,isData):
  """Return a method to check if an event passes the recommended MET filters."""
  if year==2018:
    if isData:
      return lambda e: e.Flag_goodVertices and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and e.Flag_globalSuperTightHalo2016Filter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_BadChargedCandidateFilter and e.Flag_eeBadScFilter and e.Flag_ecalBadCalibFilterV2
    else:
      return lambda e: e.Flag_goodVertices and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_BadChargedCandidateFilter and e.Flag_ecalBadCalibFilterV2
  else:
    if isData:
      return lambda e: e.Flag_goodVertices and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and e.Flag_globalSuperTightHalo2016Filter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_BadChargedCandidateFilter and e.Flag_eeBadScFilter and e.Flag_ecalBadCalibFilter
    else:
      return lambda e: e.Flag_goodVertices and e.Flag_HBHENoiseFilter and e.Flag_HBHENoiseIsoFilter and\
                       e.Flag_EcalDeadCellTriggerPrimitiveFilter and e.Flag_BadPFMuonFilter and e.Flag_BadChargedCandidateFilter and e.Flag_ecalBadCalibFilter
  
def Tau_idIso(event,i):
  raw = event.Tau_rawIso[i]
  if event.Tau_photonsOutsideSignalCone[i]/event.Tau_pt[i]<0.10:
    return 0 if raw>4.5 else 1 if raw>3.5 else 3 if raw>2.5 else 7 if raw>1.5 else 15 if raw>0.8 else 31 # VVLoose, VLoose, Loose, Medium, Tight
  return 0 if raw>4.5 else 1 if raw>3.5 else 3 # VVLoose, VLoose
  
root_dtype = {
  float: 'D',  int: 'I',  bool: 'O',
  'f':   'D',  'i': 'I',  '?':  'O',  'b': 'b'
}
num_dtype = {
  'D':   'f',  'I': 'i',  'O':  '?',  'b': 'b'
}

class TreeProducerCommon(object):
    
    def __init__(self, name):
        
        print 'TreeProducerCommon is called', name
        
        # TREE
        self.outputfile = ROOT.TFile(name, 'RECREATE')
        self.tree = TTree('tree','tree')
        
        # HISTOGRAM
        self.cutflow = TH1D('cutflow', 'cutflow',  25, 0,  25)
        self.pileup  = TH1D('pileup',  'pileup',  100, 0, 100)
        
        ## CHECK genPartFlav
        #self.flags_LTF_DM1 = TH1D('flags_LTF_DM1', "flags for l #rightarrow #tau_{h}, DM1", 18, 0, 18)
        #self.flags_LTF_DM0 = TH1D('flags_LTF_DM0', "flags for l #rightarrow #tau_{h}, DM0", 18, 0, 18)
        #self.flags_LTF_mis = TH1D('flags_LTF_mis', "flags for l #rightarrow #tau_{h}, DM1, wrong genPartFlav", 18, 0, 18)
        #self.flags_LTF_DM1_sn1 = TH1D('flags_LTF_DM1_sn1', "flags for l #rightarrow #tau_{h}, DM1 (status!=1)", 18, 0, 18)
        #self.flags_LTF_DM0_sn1 = TH1D('flags_LTF_DM0_sn1', "flags for l #rightarrow #tau_{h}, DM0 (status!=1)", 18, 0, 18)
        #self.flags_LTF_mis_sn1 = TH1D('flags_LTF_mis_sn1', "flags for l #rightarrow #tau_{h}, DM1, wrong genPartFlav (status!=1)", 18, 0, 18)
        #for hist in [self.flags_LTF_DM1, self.flags_LTF_DM0, self.flags_LTF_mis, self.flags_LTF_DM0_sn1, self.flags_LTF_DM1_sn1, self.flags_LTF_mis_sn1]:
        #  hist.GetXaxis().SetBinLabel( 1,  "isPrompt"                            )
        #  hist.GetXaxis().SetBinLabel( 2,  "isDirectPromptTauDecayProduct"       )
        #  hist.GetXaxis().SetBinLabel( 3,  "isHardProcess"                       )
        #  hist.GetXaxis().SetBinLabel( 4,  "fromHardProcess"                     )
        #  hist.GetXaxis().SetBinLabel( 5,  "isDirectHardProcessTauDecayProduct"  )
        #  hist.GetXaxis().SetBinLabel( 6,  "fromHardProcessBeforeFSR"            )
        #  hist.GetXaxis().SetBinLabel( 7,  "isFirstCopy"                         )
        #  hist.GetXaxis().SetBinLabel( 8,  "isLastCopy"                          )
        #  hist.GetXaxis().SetBinLabel( 9,  "isLastCopyBeforeFSR"                 )
        #  hist.GetXaxis().SetBinLabel(10,  "status==1"                           )
        #  hist.GetXaxis().SetBinLabel(11,  "status==23"                          )
        #  hist.GetXaxis().SetBinLabel(12,  "status==44"                          )
        #  hist.GetXaxis().SetBinLabel(13,  "status==51"                          )
        #  hist.GetXaxis().SetBinLabel(14,  "status==52"                          )
        #  hist.GetXaxis().SetBinLabel(15,  "other status"                        )
        #  hist.GetXaxis().SetLabelSize(0.041)
        #self.genmatch_corr     = TH2D("genmatch_corr","correlation between Tau_genPartFlav and genmatch",6,0,6,6,0,6)
        #self.genmatch_corr_DM0 = TH2D("genmatch_corr_DM0","correlation between Tau_genPartFlav and genmatch for DM0",6,0,6,6,0,6)
        #self.genmatch_corr_DM1 = TH2D("genmatch_corr_DM1","correlation between Tau_genPartFlav and genmatch for DM1",6,0,6,6,0,6)
        
        
        #############
        #   EVENT   #
        #############
        
        self.addBranch('run',                     int)
        self.addBranch('lumi',                    int)
        self.addBranch('event',                   int)
        self.addBranch('isData',                  bool)
        
        self.addBranch('nPU',                     int)
        self.addBranch('nTrueInt',                int)
        self.addBranch('npvs',                    int)
        self.addBranch('npvsGood',                int)
        self.addBranch('LHE_Njets',               int)
        self.addBranch('metfilter',               bool)
        
        
        ##############
        #   WEIGHT   #
        ##############
        
        self.addBranch('genweight',               float)
        self.addBranch('weight',                  float)
        self.addBranch('trigweight',              float)
        self.addBranch('puweight',                float)
        self.addBranch('zptweight',               float)
        self.addBranch('ttptweight',              float)
        self.addBranch('idisoweight_1',           float)
        self.addBranch('idisoweight_2',           float)
        self.addBranch('btagweight',              float)
        self.addBranch('btagweight_deep',         float)
        
        
        ############
        #   JETS   #
        ############
        
        self.addBranch('njets',                   int)
        self.addBranch('njets50',                 int)
        self.addBranch('ncjets',                  int)
        self.addBranch('nfjets',                  int)
        self.addBranch('nbtag',                   int)
        
        self.addBranch('jpt_1',                   float)
        self.addBranch('jeta_1',                  float)
        self.addBranch('jphi_1',                  float)
        self.addBranch('jcsvv2_1',                float)
        self.addBranch('jdeepb_1',                float)
        self.addBranch('jpt_2',                   float)
        self.addBranch('jeta_2',                  float)
        self.addBranch('jphi_2',                  float)
        self.addBranch('jcsvv2_2',                float)
        self.addBranch('jdeepb_2',                float)
        
        self.addBranch('bpt_1',                   float)
        self.addBranch('beta_1',                  float)
        self.addBranch('bpt_2',                   float)
        self.addBranch('beta_2',                  float)
        
        self.addBranch('met',                     float)
        self.addBranch('metphi',                  float)
        self.addBranch('met_corr',                float)
        self.addBranch('metphi_corr',             float)
        self.addBranch('genmet',                  float)
        self.addBranch('genmetphi',               float)
        ###self.addBranch('puppimet',                float)
        ###self.addBranch('puppimetphi',             float)
        ###self.addBranch('metsignificance',         float)
        ###self.addBranch('metcovXX',                float)
        ###self.addBranch('metcovXY',                float)
        ###self.addBranch('metcovYY',                float)
        ###self.addBranch('fixedGridRhoFastjetAll',  float)
        
        
        #############
        #   OTHER   #
        #############
        
        self.addBranch('pfmt_1',                  float)
        self.addBranch('pfmt_1_corr',             float)
        self.addBranch('pfmt_2',                  float)
        self.addBranch('m_vis',                   float)
        self.addBranch('pt_ll',                   float)
        self.addBranch('dR_ll',                   float)
        self.addBranch('dphi_ll',                 float)
        
        self.addBranch('pzetamiss',               float)
        self.addBranch('pzetavis',                float)
        self.addBranch('dzeta',                   float)
        self.addBranch('pzetamiss_corr',          float)
        self.addBranch('dzeta_corr',              float)
        
        self.addBranch('dilepton_veto',           bool)
        self.addBranch('extraelec_veto',          bool)
        self.addBranch('extramuon_veto',          bool)
        self.addBranch('lepton_vetos',            bool)
        
        self.addBranch('ngentauhads',             int)
        self.addBranch('ngentaus',                int)
        
        self.addBranch('m_genboson',              float)
        self.addBranch('pt_genboson',             float)
        
        #self.addBranch('m_taub',                    float)
        #self.addBranch('m_taumub',                  float)
        #self.addBranch('m_tauj',                    float)
        #self.addBranch('m_muj',                     float)
        #self.addBranch('m_coll_muj',                float)
        #self.addBranch('m_coll_tauj',               float)
        #self.addBranch('mt_coll_muj',               float)
        #self.addBranch('mt_coll_tauj',              float)
        #self.addBranch('m_max_lj',                  float)
        #self.addBranch('m_max_lb',                  float)
        #self.addBranch('m_mub',                     float)
        
        self.nPU[0]             = -1
        self.nTrueInt[0]        = -1
        self.LHE_Njets[0]       = -1
        
        self.weight[0]          = 1.
        self.genweight[0]       = 1.
        self.trigweight[0]      = 1.
        self.puweight[0]        = 1.
        self.idisoweight_1[0]   = 1.
        self.idisoweight_2[0]   = 1.
        self.btagweight[0]      = 1.
        self.btagweight_deep[0] = 1.
        self.zptweight[0]       = 1.
        self.ttptweight[0]      = 1.
        self.genmet[0]          = -1
        self.genmetphi[0]       = -9
        
        self.m_genboson[0]      = -1
        self.pt_genboson[0]     = -1
        
    def addBranch(self, name, dtype=float):
        """Add branch with a given name, and create an array of the same name as address."""
        if hasattr(self,name):
          print "ERROR! TreeProducerCommon.addBranch: Branch of name '%s' already exists!"%(name)
          exit(1)
        setattr(self,name,num.zeros(1,dtype=dtype))
        self.tree.Branch(name, getattr(self,name), '%s/%s'%(name,root_dtype[dtype]))
        


class DiLeptonBasicClass:
    def __init__(self, id1, pt1, iso1, id2, pt2, iso2):
        self.id1  = id1
        self.id2  = id2
        self.pt1  = pt1
        self.pt2  = pt2
        self.iso1 = iso1
        self.iso2 = iso2
        
    def __gt__(self, odilep):
        """Order dilepton pairs according to the pT of both objects first, then in isolation."""
        if   self.pt1  != odilep.pt1:  return self.pt1  > odilep.pt1  # greater = higher pT
        elif self.pt2  != odilep.pt2:  return self.pt2  > odilep.pt2  # greater = higher pT
        elif self.iso1 != odilep.iso1: return self.iso1 < odilep.iso1 # greater = smaller isolation
        elif self.iso2 != odilep.iso2: return self.iso2 < odilep.iso2 # greater = smaller isolation
        return True
    
class LeptonTauPair(DiLeptonBasicClass):
    def __gt__(self, oltau):
        """Override for tau isolation."""
        if   self.pt1  != oltau.pt1:  return self.pt1  > oltau.pt1  # greater = higher pT
        elif self.pt2  != oltau.pt2:  return self.pt2  > oltau.pt2  # greater = higher pT
        elif self.iso1 != oltau.iso1: return self.iso1 < oltau.iso1 # greater = smaller lepton isolation
        elif self.iso2 != oltau.iso2: return self.iso2 > oltau.iso2 # greater = larger tau isolation
        return True
    
class DiTauPair(DiLeptonBasicClass):
    def __gt__(self, oditau):
        """Override for tau isolation."""
        if   self.pt1  != oditau.pt1:  return self.pt1  > oditau.pt1  # greater = higher pT
        elif self.pt2  != oditau.pt2:  return self.pt2  > oditau.pt2  # greater = higher pT
        elif self.iso1 != oditau.iso1: return self.iso1 > oditau.iso1 # greater = larger tau isolation
        elif self.iso2 != oditau.iso2: return self.iso2 > oditau.iso2 # greater = larger tau isolation
        return True
    


def bestDiLepton(diLeptons):
    """Take best dilepton pair."""
    if len(diLeptons)==1:
        return diLeptons[0]
    #least_iso_highest_pt = lambda dl: (-dl.tau1_pt, -dl.tau2_pt, dl.tau2_iso, -dl.tau1_iso)
    #return sorted(diLeptons, key=lambda dl: least_iso_highest_pt(dl), reverse=False)[0]
    return sorted(diLeptons, reverse=True)[0]
    

def deltaR(eta1, phi1, eta2, phi2):
    """Compute DeltaR."""
    deta = eta1 - eta2
    dphi = deltaPhi(phi1, phi2)
    return sqrt( deta*deta + dphi*dphi )
    
def deltaPhi(phi1, phi2):
    """Computes Delta phi, handling periodic limit conditions."""
    res = phi1 - phi2
    while res > pi:
      res -= 2*pi
    while res < -pi:
      res += 2*pi
    return res
    


def genmatch(event,index,out=None):
    """Match reco tau to gen particles, as there is a bug in the nanoAOD matching
    for lepton to tau fakes of taus reconstructed as DM1."""
    genmatch  = 0
    dR_min    = 0.2
    particles = Collection(event,'GenPart')
    eta_reco  = event.Tau_eta[index]
    phi_reco  = event.Tau_phi[index]
    
    # lepton -> tau fakes
    for id in range(event.nGenPart):
      particle = particles[id]
      PID = abs(particle.pdgId)
      if (particle.status!=1 and PID!=13) or particle.pt<8: continue
      dR = deltaR(eta_reco,phi_reco,particle.eta,particle.phi)
      if dR<dR_min:
        if hasBit(particle.statusFlags,0): # isPrompt
          if   PID==11: genmatch = 1; dR_min = dR
          elif PID==13: genmatch = 2; dR_min = dR
        elif hasBit(particle.statusFlags,5): # isDirectPromptTauDecayProduct
          if   PID==11: genmatch = 3; dR_min = dR
          elif PID==13: genmatch = 4; dR_min = dR
    
    # real tau leptons
    for id in range(event.nGenVisTau):
      dR = deltaR(eta_reco,phi_reco,event.GenVisTau_eta[id],event.GenVisTau_phi[id])
      if dR<dR_min:
        dR_min = dR
        genmatch = 5
    
    return genmatch
    


def genmatchCheck(event,index,out):
    """Match reco tau to gen particles, as there is a bug in the nanoAOD matching
    for lepton to tau fakes of taus reconstructed as DM1."""
    #print '-'*80
    genmatch  = 0
    #partmatch_s1 = None
    #partmatch_sn1 = None # status != 1
    dR_min    = 1.0
    particles = Collection(event,'GenPart')
    eta_reco  = event.Tau_eta[index]
    phi_reco  = event.Tau_phi[index]
    
    # lepton -> tau fakes
    for id in range(event.nGenPart):
      particle = particles[id]
      PID = abs(particle.pdgId)
      if particle.status!=1 or particle.pt<8: continue
      #if (particle.status!=1 and PID!=13) or particle.pt<8: continue
      dR = deltaR(eta_reco,phi_reco,particle.eta,particle.phi)
      if dR<dR_min:
        if hasBit(particle.statusFlags,0): # isPrompt
          if   PID==11:
            genmatch = 1; dR_min = dR
            #if particle.status==1: partmatch_s1 = particle
            #else:                  partmatch_sn1 = particle
          elif PID==13:
            genmatch = 2; dR_min = dR
            #if particle.status==1: partmatch_s1 = particle
            #else:                  partmatch_sn1 = particle
        elif hasBit(particle.statusFlags,5): # isDirectPromptTauDecayProduct
          if   PID==11:
            genmatch = 3; dR_min = dR
            #if particle.status==1: partmatch_s1 = particle
            #else:                  partmatch_sn1 = particle
          elif PID==13:
            genmatch = 4; dR_min = dR
            #if particle.status==1: partmatch_s1 = particle
            #else:                  partmatch_sn1 = particle
        #if particle.status!=1 and particle.status!=23:
        # mother = abs(particles[particle.genPartIdxMother].pdgId) if hasattr(particle,'genPartIdxMother') and particle.genPartIdxMother>0 else 0
        # print "%3d: PID=%3d, mass=%3.1f, pt=%4.1f, status=%2d, mother=%2d, statusFlags=%5d (%16s), isPrompt=%d, isDirectPromptTauDecayProduct=%d, fromHardProcess=%1d, isHardProcessTauDecayProduct=%1d, isDirectHardProcessTauDecayProduct=%1d"%\
        # (id,particle.pdgId,particle.mass,particle.pt,particle.status,mother,particle.statusFlags,bin(particle.statusFlags),hasBit(particle.statusFlags,0),hasBit(particle.statusFlags,5),hasBit(particle.statusFlags,8),hasBit(particle.statusFlags,9),hasBit(particle.statusFlags,10))
    
    # real tau leptons
    for id in range(event.nGenVisTau):
      dR = deltaR(eta_reco,phi_reco,event.GenVisTau_eta[id],event.GenVisTau_phi[id])
      if dR<dR_min:
        dR_min = dR
        genmatch = 5
    
    ## CHECKS
    #if genmatch!=ord(event.Tau_genPartFlav[index]):
    # #mother = abs(particles[partmatch_s1.genPartIdxMother].pdgId) if hasattr(partmatch_s1,'genPartIdxMother') else 0
    # #print "gen mismatch: Tau_genPartFlav = %s, genmatch = %s, Tau_decayMode = %2s, mother = %s"%(ord(event.Tau_genPartFlav[index]),genmatch,event.Tau_decayMode[index],mother)
    # if genmatch>0 and genmatch<5 and event.Tau_decayMode[index]==1:
    #   if partmatch_s1:
    #     fillFlagHistogram(out.flags_LTF_mis,partmatch_s1)
    #   elif partmatch_sn1:
    #     fillFlagHistogram(out.flags_LTF_mis_sn1,partmatch_sn1)
    #
    ## CHECK status and flags
    #if genmatch>0 and genmatch<5:
    # if event.Tau_decayMode[index]==0:
    #   if partmatch_s1:
    #     fillFlagHistogram(out.flags_LTF_DM0,partmatch_s1)       
    #   elif partmatch_sn1:
    #     fillFlagHistogram(out.flags_LTF_DM0_sn1,partmatch_sn1)
    # elif event.Tau_decayMode[index]==1:
    #   if partmatch_s1:
    #     fillFlagHistogram(out.flags_LTF_DM1,partmatch_s1)
    #   elif partmatch_sn1:
    #     fillFlagHistogram(out.flags_LTF_DM1_sn1,partmatch_sn1)
    #     #if partmatch_sn1.status not in [23,44,52]:
    #     #  print partmatch_sn1.status
    #
    ## CHECK correlation
    #out.genmatch_corr.Fill(ord(event.Tau_genPartFlav[index]),genmatch)
    #if event.Tau_decayMode[index]==0:
    # out.genmatch_corr_DM0.Fill(ord(event.Tau_genPartFlav[index]),genmatch)
    #if event.Tau_decayMode[index]==1:
    # out.genmatch_corr_DM1.Fill(ord(event.Tau_genPartFlav[index]),genmatch)
    
    return genmatch





def fillFlagHistogram(hist,particle):
  """Fill histograms with status flags for genPartFlav check."""
  if hasBit(particle.statusFlags, 0): hist.Fill( 0) # isPrompt
  if hasBit(particle.statusFlags, 5): hist.Fill( 1) # isDirectPromptTauDecayProduct
  if hasBit(particle.statusFlags, 7): hist.Fill( 2) # isHardProcess
  if hasBit(particle.statusFlags, 8): hist.Fill( 3) # fromHardProcess
  if hasBit(particle.statusFlags,10): hist.Fill( 4) # isDirectHardProcessTauDecayProduct
  if hasBit(particle.statusFlags,11): hist.Fill( 5) # fromHardProcessBeforeFSR
  if hasBit(particle.statusFlags,12): hist.Fill( 6) # isFirstCopy
  if hasBit(particle.statusFlags,13): hist.Fill( 7) # isLastCop
  if hasBit(particle.statusFlags,14): hist.Fill( 8) # isLastCopyBeforeFSR
  if   particle.status==1:            hist.Fill( 9) # status==1
  elif particle.status==23:           hist.Fill(10) # status==23
  elif particle.status==44:           hist.Fill(11) # status==44
  elif particle.status==51:           hist.Fill(12) # status==51
  elif particle.status==52:           hist.Fill(13) # status==52
  else:                               hist.Fill(14) # other status



def extraLeptonVetos(event, muon_idxs, electron_idxs, channel):
    
    extramuon_veto = False
    extraelec_veto = False
    dilepton_veto  = False
    
    LooseMuons = [ ]
    for imuon in range(event.nMuon):
        if event.Muon_pt[imuon] < 10: continue
        if abs(event.Muon_eta[imuon]) > 2.4: continue
        if abs(event.Muon_dz[imuon]) > 0.2: continue
        if abs(event.Muon_dxy[imuon]) > 0.045: continue
        if event.Muon_pfRelIso04_all[imuon] > 0.3: continue
        if event.Muon_mediumId[imuon] > 0.5 and (imuon not in muon_idxs):
            extramuon_veto = True
        if event.Muon_pt[imuon] > 15 and event.Muon_isPFcand[imuon]: #Muon_isGlobal[imuon] and Muon_isTracker[imuon]
            LooseMuons.append(imuon)
    
    LooseElectrons = [ ]
    for ielectron in range(event.nElectron):
        if event.Electron_pt[ielectron] < 10: continue
        if abs(event.Electron_eta[ielectron]) > 2.5: continue
        if abs(event.Electron_dz[ielectron]) > 0.2: continue
        if abs(event.Electron_dxy[ielectron]) > 0.045: continue
        if event.Electron_pfRelIso03_all[ielectron] > 0.3: continue
        #if event.Electron_convVeto[ielectron] ==1 and ord(event.Electron_lostHits[ielectron]) <= 1 and event.Electron_mvaFall17Iso_WP90[ielectron] > 0.5 and (ielectron not in electron_idxs):
        if event.Electron_convVeto[ielectron] ==1 and ord(event.Electron_lostHits[ielectron]) <= 1 and getvar(event,'Electron_mvaFall17Iso_WP90')[ielectron] > 0.5 and (ielectron not in electron_idxs):
            extraelec_veto = True
        if event.Electron_pt[ielectron] > 15 and getvar(event,'Electron_mvaFall17Iso_WPL')[ielectron] > 0.5:
            LooseElectrons.append(ielectron)
    
    if channel=='mutau':
      for idx1 in LooseMuons:
        for idx2 in LooseMuons:
            if idx1 >= idx2: continue 
            dR = deltaR(event.Muon_eta[idx1], event.Muon_phi[idx1], 
                        event.Muon_eta[idx2], event.Muon_phi[idx2])
            if event.Muon_charge[idx1] * event.Muon_charge[idx2] < 0 and dR > 0.15:
                dilepton_veto = True
    
    if channel=='eletau':
      for idx1 in LooseElectrons:
        for idx2 in LooseElectrons:
            if idx1 >= idx2: continue 
            dR = deltaR(event.Electron_eta[idx1], event.Electron_phi[idx1], 
                        event.Electron_eta[idx2], event.Electron_phi[idx2])
            if event.Electron_charge[idx1] * event.Electron_charge[idx2] < 0 and dR > 0.15:
                dilepton_veto = True
    
    return extramuon_veto, extraelec_veto, dilepton_veto
    

