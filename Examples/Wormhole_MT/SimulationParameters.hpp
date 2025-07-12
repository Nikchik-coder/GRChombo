#ifndef SIMULATIONPARAMETERS_HPP_
#define SIMULATIONPARAMETERS_HPP_

#include "GRParmParse.hpp"
#include "SimulationParametersBase.hpp"
#include "Wormhole.hpp" // Use the new Wormhole class header

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
        // Load the Morris-Thorne wormhole parameters
        pp.load("throat_radius", wormhole_params.throat_radius, 1.0);
        pp.load("redshift_constant", wormhole_params.redshift_constant, 0.0);
        pp.load("K_amplitude", wormhole_params.K_amplitude, 0.0);
        pp.load("K_width", wormhole_params.K_width, 1.0);
        pp.load("regularization_radius", wormhole_params.regularization_radius, 0.1);

        wormhole_params.center = center; // Use the grid center from the base class

        // Load Apparent Horizon Finder parameters
#ifdef USE_AHFINDER
        // A good initial guess for the AH is the throat radius
        pp.load("AH_initial_guess", AH_initial_guess, wormhole_params.throat_radius);
#endif
    }

    void check_params()
    {
        warn_parameter("throat_radius", wormhole_params.throat_radius, wormhole_params.throat_radius > 0.0,
                       "should be > 0.0");
    }

    // Member variable for the initial data parameters
    Wormhole::params_t wormhole_params;

#ifdef USE_AHFINDER
    double AH_initial_guess;
#endif
};

#endif /* SIMULATIONPARAMETERS_HPP_ */