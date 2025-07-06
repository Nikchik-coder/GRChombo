/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

#ifndef WORMHOLELEVEL_HPP_
#define WORMHOLELEVEL_HPP_

#include "BHAMR.hpp"
#include "DefaultLevelFactory.hpp"
#include "GRAMRLevel.hpp"
// Problem specific includes
#include "Potential.hpp"
#include "ScalarField.hpp"

//! A class for the evolution of a collapsing wormhole, supported by a scalar field.
class WormholeLevel : public GRAMRLevel
{
    friend class DefaultLevelFactory<WormholeLevel>;
    // Inherit the constructors from GRAMRLevel
    using GRAMRLevel::GRAMRLevel;

    // Reference to the BHAMR object that contains this level
    BHAMR &m_bh_amr = dynamic_cast<BHAMR &>(m_gr_amr);

    // Typedef for the scalar field with a potential
    typedef ScalarField<Potential> ScalarFieldWithPotential;

    //! Things to do at the end of the advance step, after RK4 calculation
    virtual void specificAdvance() override;

    //! Initialize data for the field and metric variables
    virtual void initialData() override;

#ifdef CH_USE_HDF5
    //! Routines to do before outputting plot file
    virtual void prePlotLevel() override;
#endif

    //! RHS routines used at each RK4 step
    virtual void specificEvalRHS(GRLevelData &a_soln, GRLevelData &a_rhs,
                                 const double a_time) override;

    //! Tell Chombo how to tag cells for regridding
    virtual void computeTaggingCriterion(
        FArrayBox &tagging_criterion, const FArrayBox ¤t_state,
        const FArrayBox ¤t_state_diagnostics) override;

    //! To do post each time step on every level
    virtual void specificPostTimeStep() override;
};

#endif /* WORMHOLELEVEL_HPP_ */