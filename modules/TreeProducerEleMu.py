import ROOT
import math 
import numpy as num 

from TreeProducerCommon import *

class TreeProducerEleMu(TreeProducerCommon):
    
    def __init__(self, name):
        
        super(TreeProducerEleMu, self).__init__(name)
        print 'TreeProducerEleMu is called', name
        
        
        ################
        #   ELECTRON   #
        ################
        
        self.addBranch('pt_1',                float)
        self.addBranch('eta_1',               float)
        self.addBranch('phi_1',               float)
        self.addBranch('m_1',                 float)
        self.addBranch('dxy_1',               float)
        self.addBranch('dz_1',                float)
        self.addBranch('pfRelIso03_all_1',    float)
        self.addBranch('q_1',                 int)
        self.addBranch('genPartFlav_1',       int)
        self.addBranch('cutBased_1',          bool)
        self.addBranch('mvaFall17Iso_1',      float)
        self.addBranch('mvaFall17Iso_WP80_1', bool)
        self.addBranch('mvaFall17Iso_WP90_1', bool)
        self.addBranch('mvaFall17Iso_WPL_1',  bool)
        
        
        ############
        #   MUON   #
        ############
        
        self.addBranch('pt_2',                float)
        self.addBranch('eta_2',               float)
        self.addBranch('phi_2',               float)
        self.addBranch('m_2',                 float)
        self.addBranch('dxy_2',               float)
        self.addBranch('dz_2',                float)
        self.addBranch('pfRelIso04_all_2',    float)
        self.addBranch('q_2',                 int)
        self.addBranch('genPartFlav_2',       int)
        
        
        ###########
        #   TAU   #
        ###########
        
        self.addBranch('pt_3',                float)
        self.addBranch('eta_3',               float)
        self.addBranch('m_3',                 float)
        self.addBranch('decayMode_3',         int)
        self.addBranch('idAntiEle_3',         int)
        self.addBranch('idAntiMu_3',          int)
        ###self.addBranch('idDecayMode_3',       bool)
        ###self.addBranch('idDecayModeNewDMs_3', bool)
        self.addBranch('idMVAoldDM_3',        int)
        self.addBranch('idMVAoldDM2017v1_3',  int)
        self.addBranch('idMVAoldDM2017v2_3',  int)
        self.addBranch('idMVAnewDM2017v2_3',  int)
        self.addBranch('idIso_3',             int)
        self.addBranch('genPartFlav_3',       int)
        
        self.genPartFlav_1[0]  = -1
        self.genPartFlav_2[0]  = -1
        self.genPartFlav_3[0]  = -1
        
