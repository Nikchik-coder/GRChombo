#ifndef WORMSIMPARAMS_HPP_ // Renamed include guard
#define WORMSIMPARAMS_HPP_

// General includes
#include "GRParmParse.hpp"
#include "SimulationParametersBase.hpp"

// Problem specific includes:
#include "Wormhole_collapse.hpp" // Include your new class

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
        // Load wormhole parameters
        pp.load("throat_radius", wormhole_params.throat_radius, 1.0);
        pp.load("redshift_constant", wormhole_params.redshift_constant, 0.0);
        wormhole_params.center = center; // Use the center from the base class

        // Load Apparent Horizon Finder parameters
#ifdef USE_AHFINDER
        pp.load("AH_initial_guess", AH_initial_guess, wormhole_params.throat_radius);
#endif
    }

    void check_params()
    {
        warn_parameter("throat_radius", wormhole_params.throat_radius, wormhole_params.throat_radius > 0.0,
                       "should be > 0.0");
    }

    // Member variable for your new params
    Wormhole_collapse::params_t wormhole_params;

#ifdef USE_AHFINDER
    double AH_initial_guess;
#endif
};

#endif /* WORMSIMPARAMS_HPP_ */