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
    BoxLoops::loop(Constraints(m_dx, c_Ham, Interval(c_Mom1, c_Mom3)),
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