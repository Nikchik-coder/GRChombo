// In Examples/Wormhole_MT/WormholeLevel.cpp

#include "WormholeLevel.hpp"
#include "BoxLoops.hpp"
#include "CCZ4RHS.hpp"
#include "ChiTaggingCriterion.hpp"
#include "ComputePack.hpp"
#include "NewConstraints.hpp" // Using the correct, modern constraints class
#include "GammaCalculator.hpp"
#include "IntegratedMovingPunctureGauge.hpp"
#include "NanCheck.hpp"
#include "PositiveChiAndAlpha.hpp"
#include "SetValue.hpp"
#include "SixthOrderDerivatives.hpp"
#include "TraceARemoval.hpp"
#include "Wormhole.hpp"
#include "Weyl4.hpp"
#include "WeylExtraction.hpp"

void WormholeLevel::specificAdvance()
{
    BoxLoops::loop(make_compute_pack(TraceARemoval(), PositiveChiAndAlpha()),
                   m_state_new, m_state_new, INCLUDE_GHOST_CELLS);

    if (m_p.nan_check)
        BoxLoops::loop(
            NanCheck(m_dx, m_p.center, "NaNCheck in specific Advance"),
            m_state_new, m_state_new, EXCLUDE_GHOST_CELLS, disable_simd());
}

void WormholeLevel::initialData()
{
    CH_TIME("WormholeLevel::initialData");
    if (m_verbosity)
        pout() << "WormholeLevel::initialData " << m_level << endl;

    BoxLoops::loop(
        make_compute_pack(SetValue(0.), Wormhole(m_p.wormhole_params, m_dx)),
        m_state_new, m_state_new, INCLUDE_GHOST_CELLS);

    fillAllGhosts();
    BoxLoops::loop(GammaCalculator(m_dx), m_state_new, m_state_new,
                   EXCLUDE_GHOST_CELLS);

    BoxLoops::loop(Constraints(m_dx, c_Ham, Interval(c_Mom1, c_Mom3)),
                   m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);
}

      
      
#ifdef CH_USE_HDF5
void WormholeLevel::prePlotLevel()
{
    fillAllGhosts();
    // Use a compute pack to calculate both Constraints and Weyl4 at the same time
    BoxLoops::loop(
        make_compute_pack(
            Constraints(m_dx, c_Ham, Interval(c_Mom1, c_Mom3)),
            Weyl4(m_p.center, m_dx, m_p.formulation)
        ),
        m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);
}
#endif

    

    

void WormholeLevel::specificEvalRHS(GRLevelData &a_soln, GRLevelData &a_rhs,
                                  const double a_time)
{
    BoxLoops::loop(make_compute_pack(TraceARemoval(), PositiveChiAndAlpha()),
                   a_soln, a_soln, INCLUDE_GHOST_CELLS);

    if (m_p.max_spatial_derivative_order == 4)
    {
        BoxLoops::loop(
            CCZ4RHS<IntegratedMovingPunctureGauge, FourthOrderDerivatives>(
                m_p.ccz4_params, m_dx, m_p.sigma, m_p.formulation),
            a_soln, a_rhs, EXCLUDE_GHOST_CELLS);
    }
    else if (m_p.max_spatial_derivative_order == 6)
    {
        BoxLoops::loop(
            CCZ4RHS<IntegratedMovingPunctureGauge, SixthOrderDerivatives>(
                m_p.ccz4_params, m_dx, m_p.sigma, m_p.formulation),
            a_soln, a_rhs, EXCLUDE_GHOST_CELLS);
    }
}

void WormholeLevel::specificUpdateODE(GRLevelData &a_soln,
                                    const GRLevelData &a_rhs, Real a_dt)
{
    BoxLoops::loop(TraceARemoval(), a_soln, a_soln, INCLUDE_GHOST_CELLS);
}

void WormholeLevel::preTagCells()
{
    fillAllGhosts(VariableType::evolution, Interval(c_chi, c_chi));
}

void WormholeLevel::computeTaggingCriterion(
    FArrayBox &tagging_criterion, const FArrayBox &current_state,
    const FArrayBox &current_state_diagnostics)
{
    BoxLoops::loop(ChiTaggingCriterion(m_dx), current_state, tagging_criterion);
}

void WormholeLevel::specificPostTimeStep()
{
    CH_TIME("WormholeLevel::specificPostTimeStep");

    // Perform Weyl scalar extraction if requested
    if (m_p.activate_extraction)
    {
        int min_level = m_p.extraction_params.min_extraction_level();
        if (m_level == min_level)
        {
            CH_TIME("WeylExtraction");  
            // The prePlotLevel function will have already calculated Weyl4,
            // so we just need to refresh the interpolator and extract
            bool fill_ghosts = false; // Let the interpolator handle it
            m_gr_amr.m_interpolator->refresh(fill_ghosts);
            m_gr_amr.fill_multilevel_ghosts(
                VariableType::diagnostic, Interval(c_Weyl4_Re, c_Weyl4_Im),
                min_level);

            WeylExtraction my_extraction(m_p.extraction_params, m_dt, m_time, m_restart_time);
            my_extraction.execute_query(m_gr_amr.m_interpolator);
        }
    }
#ifdef USE_AHFINDER
    if (m_bh_amr.m_ah_finder.need_diagnostics(m_dt, m_time))
    {
        fillAllGhosts();
        BoxLoops::loop(Constraints(m_dx, c_Ham, Interval(c_Mom1, c_Mom3)),
                       m_state_new, m_state_diagnostics, EXCLUDE_GHOST_CELLS);
    }
    if (m_p.AH_activate && m_level == m_p.AH_params.level_to_run)
        m_bh_amr.m_ah_finder.solve(m_dt, m_time, m_restart_time);
#endif
}