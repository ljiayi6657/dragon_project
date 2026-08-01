PARAM_MAP = {
    # Output
    "feedback": "//Output/feedback",

    # Observer and grid
    "observerX": "//Grid/Observer/x",
    "observerY": "//Grid/Observer/y",
    "observerZ": "//Grid/Observer/z",
    "Rmax": "//Grid/Rmax",
    "L": "//Grid/L",
    "DimX": "//Grid/DimX",
    "DimY": "//Grid/DimY",
    "DimZ": "//Grid/DimZ",
    "Ekmin": "//Grid/Ekmin",
    "Ekmax": "//Grid/Ekmax",
    "Ekfactor": "//Grid/Ekfactor",
    "Zmax": "//Grid/NuclearChain/Zmax",
    "Zmin": "//Grid/NuclearChain/Zmin",

    # Algorithm
    "Nrept": "//Algorithm/OpSplit/Nrept",
    "Dtfactor": "//Algorithm/OpSplit/Dtfactor",
    "Dtmin": "//Algorithm/OpSplit/Dtmin",
    "Dtmax": "//Algorithm/OpSplit/Dtmax",

    # Diffusion and reacceleration
    "D0": "//Galaxy/Diffusion/D0_1e28",
    "DiffRefRig": "//Galaxy/Diffusion/DiffRefRig",
    "Delta": "//Galaxy/Diffusion/Delta",
    "VariableDelta": "//Galaxy/Diffusion/VariableDelta",
    "DiffusionThreshold": "//Galaxy/Diffusion/DiffusionThreshold",
    "deltaA": "//Galaxy/Diffusion/deltaA",
    "deltaB": "//Galaxy/Diffusion/deltaB",
    "deltaZ": "//Galaxy/Diffusion/deltaZ",
    "zt": "//Galaxy/Diffusion/zt",
    "etaT": "//Galaxy/Diffusion/etaT",
    "vA": "//Galaxy/Reacceleration/vA_kms",

    # Magnetic field
    "B0disk": "//Galaxy/MagneticField/B0disk",
    "B0halo": "//Galaxy/MagneticField/B0halo",
    "B0turb": "//Galaxy/MagneticField/B0turb",

    # Flux normalization
    "protEnergy": "//CR/ProtNormEn_GeV",
    "electronEnergy": "//CR/ElNormEn_GeV",
    "protFlux": "//CR/ProtNormFlux",
    "electronFlux": "//CR/ElNormFlux",
    "extraEnergy": "//CR/ElNormEnExtra_GeV",
    "extraFlux": "//CR/ElNormFluxExtra",

    # Nuclei injection
    "nucAlpha0": "//CR/InjectionIndexAllNuclei/alpha_0",
    "nucRho0": "//CR/InjectionIndexAllNuclei/rho_0",
    "nucAlpha1": "//CR/InjectionIndexAllNuclei/alpha_1",
    "nucRho1": "//CR/InjectionIndexAllNuclei/rho_1",
    "nucAlpha2": "//CR/InjectionIndexAllNuclei/alpha_2",
    "nucRho2": "//CR/InjectionIndexAllNuclei/rho_2",
    "nucAlpha3": "//CR/InjectionIndexAllNuclei/alpha_3",

    # Electron injection
    "electronRho0": "//CR/InjectionIndexElectrons/rho_0",
    "electronRho1": "//CR/InjectionIndexElectrons/rho_1",
    "electronRho2": "//CR/InjectionIndexElectrons/rho_2",
    "electronAlpha0": "//CR/InjectionIndexElectrons/alpha_0",
    "electronAlpha1": "//CR/InjectionIndexElectrons/alpha_1",
    "electronAlpha2": "//CR/InjectionIndexElectrons/alpha_2",
    "electronAlpha3": "//CR/InjectionIndexElectrons/alpha_3",
    "electronCutoff": "//CR/InjectionIndexElectrons/CutoffRigEl",

    # Extra-component injection
    "extraRho0": "//CR/InjectionIndexExtraComponent/rho_0",
    "extraAlpha0": "//CR/InjectionIndexExtraComponent/alpha_0",
    "extraAlpha1": "//CR/InjectionIndexExtraComponent/alpha_1",
    "extraCutoff": "//CR/InjectionIndexExtraComponent/CutoffRigExtra",
}


NODE_MAP = {
    "lepton": "//Grid/NuclearChain/PropLepton",
    "extraComponent": "//Grid/NuclearChain/PropExtraComponent",
}
