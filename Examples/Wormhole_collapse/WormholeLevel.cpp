/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

#include "WormholeLevel.hpp"
#include "BoxLoops.hpp"
#include "ComputePack.hpp"
#include "NanCheck.hpp"
#include "PositiveChiAndAlpha.hpp"
#include "SetValue.hpp"
#include "TraceARemoval.hpp"

// Problem specific includes
#include "ChiTaggingCriterion.hpp"
#include "MatterCCZ4RHS.hpp"
#include "NewMatterConstraints.hpp"
#include "Weyl4.hpp"
#include "WeylExtraction.hpp"
#include "WormholeICs.hpp"
#include "ChiAndPhiTaggingCriterion.hpp" // <-- ADD THIS LINE

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

    BoxLoops::loop(SetValue(0.), m_state_new, m_state_new, INCLUDE_GHOST_CELLS);

    WormholeICs wormhole_ICs(m_p.wormhole_params, m_dx);
    BoxLoops::loop(wormhole_ICs, m_state_new, m_state_new, INCLUDE_GHOST_CELLS);
}

#ifdef CH_USE_HDF5
// Things to do before outputting a plot file
void WormholeLevel::prePlotLevel()
{
    fillAllGhosts();
    Potential potential(m_p.potential_params);
    ScalarFieldWithPotential scalar_field(potential);
    BoxLoops::loop(
        MatterConstraints<ScalarFieldWithPotential>(
            scalar_field, m_dx, m_p.G_Newton, c_Ham, Interval(c_Mom1, c_Mom3)),
        m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);

    // Calculate Weyl4 scalar for plotting
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
    ScalarFieldWithPotential scalar_field(potential);
    if (m_p.max_spatial_derivative_order == 4)
    {
        MatterCCZ4RHS<ScalarFieldWithPotential, MovingPunctureGauge,
                      FourthOrderDerivatives>
            my_ccz4_matter(scalar_field, m_p.ccz4_params, m_dx, m_p.sigma,
                           m_p.formulation, m_p.G_Newton);
        BoxLoops::loop(my_ccz4_matter, a_soln, a_rhs, EXCLUDE_GHOST_CELLS);
    }
}

void WormholeLevel::computeTaggingCriterion(
    FArrayBox &tagging_criterion, const FArrayBox &current_state,
    const FArrayBox &current_state_diagnostics)
{
    // The ChiAndPhiTaggingCriterion is used here based on the likely
    // physics of the wormhole collapse example.
    BoxLoops::loop(ChiAndPhiTaggingCriterion(m_dx, m_p.regrid_thresholds[m_level],
                                              m_p.regrid_thresholds[m_level]),
                   current_state, tagging_criterion);
}

// To do post each time step on every level
void WormholeLevel::specificPostTimeStep()
{
    CH_TIME("WormholeLevel::specificPostTimeStep");
    bool first_step = (m_time == 0.);

    if (m_p.activate_extraction)
    {
        int min_level = m_p.extraction_params.min_extraction_level();
        bool calculate_weyl = at_level_timestep_multiple(min_level);
        if (calculate_weyl)
        {
            fillAllGhosts();
            BoxLoops::loop(
                Weyl4(m_p.extraction_params.center, m_dx, m_p.formulation),
                m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);

            if (m_level == min_level)
            {
                CH_TIME("WeylExtraction");
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
}