/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

// General includes common to most GR problems
#include "WormholeLevel.hpp"
#include "AMRReductions.hpp"
#include "BoxLoops.hpp"
#include "CustomExtraction.hpp"
#include "NanCheck.hpp"
#include "PositiveChiAndAlpha.hpp"
#include "SixthOrderDerivatives.hpp"
#include "TraceARemoval.hpp"

// For RHS update
#include "MatterCCZ4RHS.hpp"

// For constraints calculation
#include "NewMatterConstraints.hpp"

// For tag cells
#include "FixedGridsTaggingCriterion.hpp"

// For gravitational wave extraction
#include "Weyl4.hpp"
#include "WeylExtraction.hpp"

// Problem specific includes
#include "ComputePack.hpp"
#include "GammaCalculator.hpp"
#include "WormholeICs.hpp"
#include "Potential.hpp"
#include "ScalarField.hpp"
#include "SetValue.hpp"

// Things to do at each advance step, after the RK4 is calculated
void WormholeLevel::specificAdvance()
{
    // Enforce trace free A_ij and positive chi and alpha
    BoxLoops::loop(
        make_compute_pack(TraceARemoval(),
                          PositiveChiAndAlpha(m_p.min_chi, m_p.min_lapse)),
        m_state_new, m_state_new, INCLUDE_GHOST_CELLS);

    // Check for nan's
    if (m_p.nan_check)
        BoxLoops::loop(
            NanCheck(m_dx, m_p.center, "NaNCheck in specific Advance"),
            m_state_new, m_state_new, EXCLUDE_GHOST_CELLS, disable_simd());
}

// Initial data for field and metric variables
void WormholeLevel::initialData()
{
    CH_TIME("WormholeLevel::initialData");
    if (m_verbosity)
        pout() << "WormholeLevel::initialData " << m_level << endl;
    
    // Instantiate your wormhole ICs class
    WormholeICs wormhole_ICs(m_p.wormhole_params, m_dx);

    // Set all variables on the grid
    BoxLoops::loop(wormhole_ICs, m_state_new, m_state_new, INCLUDE_GHOST_CELLS);
}

// Things to do when restarting from a checkpoint, including
// restart from the initial condition solver output
void WormholeLevel::postRestart()
{
    // On restart calculate the constraints on every level
    fillAllGhosts();
    Potential potential(m_p.potential_params);
    WormholeWithPotential wormhole_with_potential(potential);
    BoxLoops::loop(
        MatterConstraints<WormholeWithPotential>(
            wormhole_with_potential, m_dx, m_p.G_Newton, c_Ham, Interval(c_Mom1, c_Mom3)),
        m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);

    // Use AMR Interpolator and do lineout data extraction
    // pass the boundary params so that we can use symmetries
    AMRInterpolator<Lagrange<2>> interpolator(
        m_gr_amr, m_p.origin, m_p.dx, m_p.boundary_params, m_p.verbosity);

    // this should fill all ghosts including the boundary ones according
    // to the conditions set in params.txt
    interpolator.refresh();

    // restart works from level 0 to highest level, so want this to happen last
    // on finest level
    int write_out_level = m_p.max_level;    
    if (m_level == write_out_level)
    {
        // AMRReductions for diagnostic variables
        AMRReductions<VariableType::diagnostic> amr_reductions_diagnostic(
            m_gr_amr);
        double L2_Ham = amr_reductions_diagnostic.norm(c_Ham);
        double L2_Mom = amr_reductions_diagnostic.norm(Interval(c_Mom1, c_Mom3));

        // only on rank zero write out the result
        if (procID() == 0)
        {
            pout() << "The initial norm of the constraint vars on restart is "
                   << L2_Ham << " for the Hamiltonian constraint and " << L2_Mom
                   << " for the momentum constraints" << endl;
        }

        // set up the query and execute it
        int num_points = 3 * m_p.ivN[0];
        CustomExtraction constraint_extraction(c_Ham, c_Mom, num_points, m_p.L,
                                               m_p.center, m_dt, m_time);
        constraint_extraction.execute_query(
            &interpolator, m_p.data_path + "constraint_lineout");
    }
}

#ifdef CH_USE_HDF5
// Things to do before outputting a checkpoint file
void WormholeLevel::prePlotLevel()
{
    fillAllGhosts();
    Potential potential(m_p.potential_params);
    WormholeWithPotential wormhole_with_potential(potential);
    BoxLoops::loop(
        MatterConstraints<WormholeWithPotential>(
            wormhole_with_potential, m_dx, m_p.G_Newton, c_Ham, Interval(c_Mom1, c_Mom3)),
        m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);
    
    // Calculate Weyl4 scalar for gravitational wave extraction
    if (m_p.activate_extraction)
    {
        BoxLoops::loop(
            Weyl4(m_p.extraction_params.center, m_dx, m_p.formulation),
            m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);
    }
}
#endif

// Things to do in RHS update, at each RK4 step
void WormholeLevel::specificEvalRHS(GRLevelData &a_soln, GRLevelData &a_rhs,
                                       const double a_time)
{
    // Enforce trace free A_ij and positive chi and alpha
    BoxLoops::loop(
        make_compute_pack(TraceARemoval(),
                          PositiveChiAndAlpha(m_p.min_chi, m_p.min_lapse)),
        a_soln, a_soln, INCLUDE_GHOST_CELLS);

    // Calculate MatterCCZ4 right hand side with matter_t = ScalarField
    Potential potential(m_p.potential_params);
    WormholeWithPotential wormhole_with_potential(potential);
    if (m_p.max_spatial_derivative_order == 4)
    {
        MatterCCZ4RHS<WormholeWithPotential, MovingPunctureGauge,
                      FourthOrderDerivatives>
            my_ccz4_matter(wormhole_with_potential, m_p.ccz4_params, m_dx, m_p.sigma,
                           m_p.formulation, m_p.G_Newton);
        BoxLoops::loop(my_ccz4_matter, a_soln, a_rhs, EXCLUDE_GHOST_CELLS);
    }
    else if (m_p.max_spatial_derivative_order == 6)
    {
        MatterCCZ4RHS<WormholeWithPotential, MovingPunctureGauge,
                      SixthOrderDerivatives>
            my_ccz4_matter(wormhole_with_potential, m_p.ccz4_params, m_dx, m_p.sigma,
                           m_p.formulation, m_p.G_Newton);
        BoxLoops::loop(my_ccz4_matter, a_soln, a_rhs, EXCLUDE_GHOST_CELLS);
    }
}

// Things to do at ODE update, after soln + rhs
void WormholeLevel::specificUpdateODE(GRLevelData &a_soln,
                                         const GRLevelData &a_rhs, Real a_dt)
{
    // Enforce trace free A_ij
    BoxLoops::loop(TraceARemoval(), a_soln, a_soln, INCLUDE_GHOST_CELLS);
}

void WormholeLevel::preTagCells()
{
    // we don't need any ghosts filled for the fixed grids tagging criterion
    // used here so don't fill any
}

void WormholeLevel::computeTaggingCriterion(
    FArrayBox &tagging_criterion, const FArrayBox &current_state,
    const FArrayBox &current_state_diagnostics)
{
    // If using symmetry of the box, adjust physical length
    int symmetry = 1;
    BoxLoops::loop(
        FixedGridsTaggingCriterion(m_dx, m_level, m_p.L / symmetry, m_p.center),
        current_state, tagging_criterion);
}

void WormholeLevel::specificPostTimeStep()
{
    CH_TIME("WormholeLevel::specificPostTimeStep");

    bool first_step = (m_time == 0.);

    // Gravitational wave extraction
    if (m_p.activate_extraction)
    {
        int min_level = m_p.extraction_params.min_extraction_level();
        bool calculate_weyl = at_level_timestep_multiple(min_level);
        if (calculate_weyl)
        {
            // Populate the Weyl Scalar values on the grid
            fillAllGhosts();
            BoxLoops::loop(
                Weyl4(m_p.extraction_params.center, m_dx, m_p.formulation),
                m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);

            // Do the extraction on the min extraction level
            if (m_level == min_level)
            {
                CH_TIME("WeylExtraction");
                // Now refresh the interpolator and do the interpolation
                bool fill_ghosts = false;
                m_gr_amr.m_interpolator->refresh(fill_ghosts);
                m_gr_amr.fill_multilevel_ghosts(
                    VariableType::diagnostic, Interval(c_Weyl4_Re, c_Weyl4_Im),
                    min_level);
                WeylExtraction my_extraction(m_p.extraction_params, m_dt,
                                             m_time, first_step,
                                             m_restart_time);
                my_extraction.execute_query(m_gr_amr.m_interpolator);
            }
        }
    }

#ifdef USE_AHFINDER
    if (m_p.AH_activate && m_level == m_p.AH_params.level_to_run)
        m_bh_amr.m_ah_finder.solve(m_dt, m_time, m_restart_time);
#endif
}
