// In Examples/Wormhole_collapse/SimulationParameters.hpp

#ifndef SIMULATIONPARAMETERS_HPP_
#define SIMULATIONPARAMETERS_HPP_

// General includes
#include "GRParmParse.hpp"
#include "SimulationParametersBase.hpp"

// Problem specific includes:
#include "Wormhole_collapse.hpp" // The new initial data class

class SimulationParameters : public SimulationParametersBase
{
  public:
    SimulationParameters(GRParmParse &pp) : SimulationParametersBase(pp)
    {
        read_params(pp);
        check_params();
    }

    /// Read parameters from the parameter file
    void read_params(GRParmParse &pp)
    {
        // Load the mass parameter for the Schwarzschild wormhole
        pp.load("wormhole_mass", wormhole_params.mass, 1.0);
        wormhole_params.center = center; // Use the center from the base class

        // Load Apparent Horizon Finder parameters
#ifdef USE_AHFINDER
        // A good initial guess for the AH is the Schwarzschild radius
        double AH_default_guess = 2.0 * wormhole_params.mass;
        pp.load("AH_initial_guess", AH_initial_guess, AH_default_guess);
#endif
    }

    void check_params()
    {
        warn_parameter("wormhole_mass", wormhole_params.mass, wormhole_params.mass > 0.0,
                       "should be > 0.0");
    }

    // Member variable for the initial data parameters
    Wormhole_collapse::params_t wormhole_params;

#ifdef USE_AHFINDER
    double AH_initial_guess;
#endif
};

#endif /* SIMULATIONPARAMETERS_HPP_ */