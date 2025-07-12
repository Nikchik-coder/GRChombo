// In Examples/Wormhole_MT/Wormhole.impl.hpp

#if !defined(WORMHOLE_HPP_)
#error "This file should only be included through Wormhole.hpp"
#endif

#ifndef WORMHOLE_IMPL_HPP_
#define WORMHOLE_IMPL_HPP_

#include "DimensionDefinitions.hpp"
#include "TensorAlgebra.hpp"
#include "simd.hpp"

template <class data_t>
void Wormhole::compute(Cell<data_t> current_cell) const
{
    using namespace TensorAlgebra;

    // 1. Get Parameters and Coordinates
    Coordinates<data_t> coords(current_cell, m_dx, m_params.center);
    data_t l = coords.get_radius(); // This is the proper radial distance
    double b0 = m_params.throat_radius;
    double Phi0 = m_params.redshift_constant;
    // V-- THE REGULARIZATION PARAMETER --V
    double eta = m_params.regularization_radius; // A small radius to smooth the cusp
    const double epsilon = 1e-6;

    // BSSN variables
    Vars<data_t> vars;

    // --- Implementation of the Regularized, Singularity-Free Metric ---

    // 2. Calculate the BSSN variables
    data_t l2 = l * l;
    double b02 = b0 * b0;
    double eta2 = eta * eta;

    // V-- THE REGULARIZATION FIX --V
    // Replace l^2 with (l^2 + eta^2) in all denominators to prevent blow-ups at l=0
    data_t l2_reg = l2 + eta2;
    data_t one_plus_b02_over_l2_reg = 1.0 + b02 / l2_reg;
    // A-- THE REGULARIZATION FIX --A
    
    // Conformal factor chi = (1 + b0^2/(l^2+eta^2))^(-2/3)
    vars.chi = pow(one_plus_b02_over_l2_reg, -2.0/3.0);

    // Conformal metric h_ij
    Tensor<1, data_t> n;
    n[0] = coords.x / simd_max(l, epsilon);
    n[1] = coords.y / simd_max(l, epsilon);
    n[2] = coords.z / simd_max(l, epsilon);

    FOR(i, j)
    {
        // V-- THE REGULARIZATION FIX --V
        data_t gamma_ij = (-b02 / l2_reg) * n[i] * n[j] + one_plus_b02_over_l2_reg * (i==j);
        // A-- THE REGULARIZATION FIX --A
        vars.h[i][j] = vars.chi * gamma_ij;
    }

    // Set the lapse, shift, and trace-free extrinsic curvature
    vars.lapse = exp(Phi0);
    FOR(i) { vars.shift[i] = 0.0; }
    FOR(i,j) { vars.A[i][j] = 0.0; }

    // 3. Set the initial "velocity" for collapse via Extrinsic Curvature
    // The throat is at l=0, so the Gaussian is centered there.
    data_t K_profile = m_params.K_amplitude * exp(-l2 / (m_params.K_width * m_params.K_width));
    vars.K = K_profile;

    // 4. Store the calculated values
    current_cell.store_vars(vars);
}

#endif /* WORMHOLE_IMPL_HPP_ */