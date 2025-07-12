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
    data_t r = coords.get_radius();
    double b0 = m_params.throat_radius;
    double Phi0 = m_params.redshift_constant;
    const double epsilon = 1e-6;
    r = simd_max(r, b0 + epsilon); // Ensure r is safely outside the throat

    // 2. Calculate BSSN variables for a Morris-Thorne wormhole
    Vars<data_t> vars;
    vars.lapse = exp(Phi0);
    FOR(i) { vars.shift[i] = 0.0; }
    vars.chi = 1.0;

    data_t b_r = b0 * b0 / r;
    data_t g_rr_inv = 1.0 - b_r / r;
    g_rr_inv = simd_max(g_rr_inv, epsilon);
    data_t g_rr = 1.0 / g_rr_inv;

    Tensor<1, data_t> n;
    n[0] = coords.x / r;
    n[1] = coords.y / r;
    n[2] = coords.z / r;

    FOR(i, j)
    {
        vars.h[i][j] = (i == j ? 1.0 : 0.0) + (g_rr - 1.0) * n[i] * n[j];
    }

    // 3. Set the initial "velocity" for collapse via Extrinsic Curvature
    data_t K_profile = m_params.K_amplitude * exp(-(r - b0) * (r - b0) / (m_params.K_width * m_params.K_width));
    vars.K = K_profile;
    FOR(i, j) { vars.A[i][j] = 0.0; }

    // 4. Store the calculated values
    current_cell.store_vars(vars);
}

#endif /* WORMHOLE_IMPL_HPP_ */