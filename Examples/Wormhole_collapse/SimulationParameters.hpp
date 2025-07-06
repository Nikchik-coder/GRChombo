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
#include "Potential.hpp"
#include "WormholeICs.hpp"

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
        wormhole_params.center = center; // already read in SimulationParametersBase
        pp.load("G_Newton", G_Newton, 1.0);
        pp.load("scalar_amplitude", wormhole_params.scalar_amplitude, 1e-12);
        pp.load("throat_radius", wormhole_params.throat_radius, 1.0);
        pp.load("wormhole_mass", wormhole_params.mass, 1.0);
        pp.load("scalar_mass", potential_params.scalar_mass, 0.2);

        // Gravitational wave extraction parameters
        pp.load("activate_extraction", activate_extraction, false);
        if (activate_extraction)
        {
            // The SphericalExtraction class reads its own parameters,
            // but we need to load them into a params object here
            // to pass to the WeylExtraction constructor.
            extraction_params.num_extraction_radii = 0;
            pp.load("num_extraction_radii", extraction_params.num_extraction_radii, 1);
            if (extraction_params.num_extraction_radii > 0)
            {
                pp.load("extraction_radii", extraction_params.extraction_radii,
                        extraction_params.num_extraction_radii);
                pp.load("extraction_levels", extraction_params.extraction_levels,
                        extraction_params.num_extraction_radii);
                pp.load("num_points_phi", extraction_params.num_points_phi, 24);
                pp.load("num_points_theta", extraction_params.num_points_theta, 37);
                pp.load("num_modes", extraction_params.num_modes, 1);
                std::vector<int> extraction_modes_vect(2 * extraction_params.num_modes);
                pp.load("modes", extraction_modes_vect, 2 * extraction_params.num_modes);
                extraction_params.modes.resize(extraction_params.num_modes);
                for (int i = 0; i < extraction_params.num_modes; ++i)
                {
                    extraction_params.modes[i].first = extraction_modes_vect[2 * i];
                    extraction_params.modes[i].second = extraction_modes_vect[2 * i + 1];
                }
                pp.load("extraction_center", extraction_params.center, center);
            }
        }

#ifdef USE_AHFINDER
        // Apparent horizon finder
        pp.load("AH_initial_guess", AH_initial_guess, 2.0 * wormhole_params.mass);
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
                       wormhole_params.mass < 0.2 * L,
                       "gives a wormhole size that may be too large for the domain");
        warn_parameter("throat_radius", wormhole_params.throat_radius,
                       wormhole_params.throat_radius < 0.2 * L,
                       "gives a throat radius that may be too large for the domain");
    }

    // Initial data for matter, potential and wormhole
    double G_Newton;
    WormholeICs::params_t wormhole_params;
    Potential::params_t potential_params;

    // Gravitational wave extraction
    bool activate_extraction;
    spherical_extraction_params_t extraction_params;

#ifdef USE_AHFINDER
    double AH_initial_guess;
#endif
};

#endif /* SIMULATIONPARAMETERS_HPP_ */