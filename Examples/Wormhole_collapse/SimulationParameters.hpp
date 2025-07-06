/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

#ifndef SIMULATIONPARAMETERS_HPP_
#define SIMULATIONPARAMETERS_HPP_

// General includes
#include "GRParmParse.hpp"
#include "SimulationParametersBase.hpp"

// Problem specific includes:
#include "WormholeICs.hpp"
#include "Potential.hpp"

// For gravitational wave extraction
#include "SphericalExtraction.hpp"

class SimulationParameters : public SimulationParametersBase
{
  public:
    SimulationParameters(GRParmParse &pp) : SimulationParametersBase(pp)
    {
        // read the problem specific params
        read_params(pp);
        check_params();
    }

    void read_params(GRParmParse &pp)
    {
        // Initial wormhole data
        wormhole_params.center =
            center; // already read in SimulationParametersBase
        pp.load("G_Newton", G_Newton, 1.0);
        pp.load("scalar_amplitude", wormhole_params.scalar_amplitude, 0.1);
        pp.load("throat_radius", wormhole_params.throat_radius, 1.0);
        pp.load("wormhole_mass", wormhole_params.mass, 1.0);
        pp.load("scalar_mass", potential_params.scalar_mass, 0.1);

        // Gravitational wave extraction parameters
        pp.load("activate_extraction", activate_extraction, false);
        if (activate_extraction)
        {
            pp.load("extraction_center", extraction_params.center, center);
            pp.load("num_extraction_radii", extraction_params.num_extraction_radii, 1);
            pp.load("extraction_radii", extraction_params.extraction_radii, 
                     extraction_params.num_extraction_radii);
            pp.load("extraction_levels", extraction_params.extraction_levels, 
                     extraction_params.num_extraction_radii);
            pp.load("num_points_phi", extraction_params.num_points_phi, 24);
            pp.load("num_points_theta", extraction_params.num_points_theta, 37);
            pp.load("extraction_interval", extraction_params.extraction_interval, 1);
            pp.load("extraction_subpath", extraction_params.extraction_subpath, 
                     std::string("data"));
        }

#ifdef USE_AHFINDER
        double AH_guess =
            8. * wormhole_params.scalar_amplitude * wormhole_params.scalar_amplitude;
        pp.load("AH_initial_guess", AH_initial_guess, AH_guess);
#endif
    }

    void check_params()
    {
        warn_parameter("scalar_mass", potential_params.scalar_mass,
                       potential_params.scalar_mass <
                           0.2 / coarsest_dx / dt_multiplier,
                       "oscillations of scalar field do not appear to be "
                       "resolved on coarsest level");
        warn_parameter("wormhole_mass", wormhole_params.mass,
                       wormhole_params.mass < 0.1 * L,
                       "gives a wormhole size greater than 0.1 times the domain L");
        warn_parameter("throat_radius", wormhole_params.throat_radius,
                       wormhole_params.throat_radius < 0.1 * L,
                       "gives a throat radius greater than 0.1 times the domain L");
    }

    // Initial data for matter and potential and wormhole
    double G_Newton;
    WormholeICs::params_t wormhole_params;
    Potential::params_t potential_params;

    // Gravitational wave extraction
    bool activate_extraction;
    SphericalExtraction::params_t extraction_params;

#ifdef USE_AHFINDER
    double AH_initial_guess;
#endif
};

#endif /* SIMULATIONPARAMETERS_HPP_ */
