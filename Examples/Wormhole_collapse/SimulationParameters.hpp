/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

#ifndef SIMULATIONPARAMETERS_HPP_
#define SIMULATIONPARAMETERS_HPP_

#include "GRParmParse.hpp"
#include "SimulationParametersBase.hpp"
#include "Potential.hpp"
#include "WormholeICs.hpp"
#include "SphericalExtraction.hpp"

class SimulationParameters : public SimulationParametersBase
{
  public:
    SimulationParameters(GRParmParse &pp) : SimulationParametersBase(pp)
    {
        read_params(pp);
        check_params();
    }

    void read_params(GRParmParse &pp)
    {
        // Initial data for a Gaussian pulse in chi
        pp.load("amplitude", wormhole_params.amplitude, 0.1);
        pp.load("width", wormhole_params.width, 1.0);
        wormhole_params.center = center;

        // Scalar field potential params
        pp.load("scalar_mass", potential_params.scalar_mass, 0.2);
        // Add G_Newton back
        pp.load("G_Newton", G_Newton, 1.0);

        // Gravitational wave extraction parameters
        pp.load("activate_extraction", activate_extraction, false);
        if (activate_extraction)
        {
            pp.load("num_extraction_radii", extraction_params.num_extraction_radii, 0);
            if (extraction_params.num_extraction_radii > 0)
            {
                pp.load("extraction_radii", extraction_params.extraction_radii, extraction_params.num_extraction_radii);
                pp.load("extraction_levels", extraction_params.extraction_levels, extraction_params.num_extraction_radii);
                pp.load("num_points_phi", extraction_params.num_points_phi, 24);
                pp.load("num_points_theta", extraction_params.num_points_theta, 37);
                pp.load("num_modes", extraction_params.num_modes, 1);
                
                std::vector<int> modes_vector;
                pp.load("modes", modes_vector, extraction_params.num_modes * 2);
                extraction_params.modes.resize(extraction_params.num_modes);
                for(int i=0; i < extraction_params.num_modes; ++i)
                {
                    extraction_params.modes[i] = {modes_vector[2*i], modes_vector[2*i+1]};
                }

                pp.load("extraction_center", extraction_params.center, center);
            }
        }
    }

    void check_params() { /* Basic checks can go here */ }

    // Initial data and matter parameters
    WormholeICs::params_t wormhole_params;
    Potential::params_t potential_params;
    double G_Newton; // Added back
    
    // Gravitational wave extraction
    bool activate_extraction;
    spherical_extraction_params_t extraction_params;

#ifdef USE_AHFINDER
    double AH_initial_guess = 2.0;
#endif
};

#endif /* SIMULATIONPARAMETERS_HPP_ */