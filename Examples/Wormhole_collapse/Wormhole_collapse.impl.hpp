// In Examples/Wormhole/Wormhole.impl.hpp

#if !defined(WORMHOLE_COLLAPSE_HPP_)
#error "This file should only be included through Wormhole_collapse.hpp"
#endif

#ifndef WORMHOLE_IMPL_HPP_
#define WORMHOLE_IMPL_HPP_

#include "DimensionDefinitions.hpp"
#include "CoordinateTransformations.hpp"
#include "TensorAlgebra.hpp"

// This is the main compute function called for each cell
template <class data_t> void Wormhole_collapse::compute(Cell<data_t> current_cell) const
{
    using namespace CoordinateTransformations;
    using namespace TensorAlgebra;

    Vars<data_t> vars;
    Coordinates<data_t> coords(current_cell, m_dx, m_params.center);

    // Get the metric, extrinsic curvature, and lapse in spherical coordinates
    Tensor<2, data_t> spherical_g;
    Tensor<2, data_t> spherical_K;
    data_t wormhole_lapse;
    
    compute_wormhole(spherical_g, spherical_K, wormhole_lapse, coords);
    
    // Convert spherical components to Cartesian components at this cell's location
    data_t x = coords.x;
    data_t y = coords.y;
    data_t z = coords.z;
    vars.h = spherical_to_cartesian_LL(spherical_g, x, y, z);
    vars.A = spherical_to_cartesian_LL(spherical_K, x, y, z);

    // --- The rest is identical to the KerrBH example ---
    data_t deth = compute_determinant(vars.h);
    auto h_UU = compute_inverse_sym(vars.h);
    vars.chi = pow(deth, -1. / 3.);

    vars.K = compute_trace(vars.A, h_UU);
    make_trace_free(vars.A, vars.h, h_UU);

    FOR(i, j)
    {
        vars.h[i][j] *= vars.chi;
        vars.A[i][j] *= vars.chi;
    }

    vars.lapse = wormhole_lapse; 
    FOR(i) { vars.shift[i] = 0.0; } 

    current_cell.store_vars(vars);
}

// This is where you define your wormhole metric components
// THIS SHOULD BE THE ONLY VERSION OF THIS FUNCTION IN THE FILE
template <class data_t>
void Wormhole_collapse::compute_wormhole(Tensor<2, data_t> &spherical_g,
                                Tensor<2, data_t> &spherical_K,
                                data_t &wormhole_lapse,
                                const Coordinates<data_t> &coords) const
{
    // Get parameters
    double b0 = m_params.throat_radius;
    double phi_0 = m_params.redshift_constant;

    // Get coordinates from the Coordinates object
    data_t r = coords.get_radius();

    // Avoid division by zero at the center
    static const double minimum_r = 1e-6;
    r = simd_max(r, minimum_r);
    data_t r_sq = r * r;

    // The shape function b(r) = b0^2 / r.
    data_t b_over_r = b0 * b0 / r_sq;

    // Calculate sin_theta^2 manually
    data_t rho_sq = coords.x * coords.x + coords.y * coords.y;
    data_t sin_theta_sq = rho_sq / r_sq;
    sin_theta_sq = simd_conditional(r_sq > simd<double>(1e-12), sin_theta_sq, 0.0);

    // The metric components in spherical coordinates (r, theta, phi)
    FOR(i, j) { spherical_g[i][j] = 0.0; }
    spherical_g[0][0] = 1.0 / (1.0 - b_over_r); // g_rr
    spherical_g[1][1] = r_sq;                   // g_thetatheta
    spherical_g[2][2] = r_sq * sin_theta_sq;    // g_phiphi

    // For a time-symmetric initial slice, the extrinsic curvature is zero
    FOR(i, j) { spherical_K[i][j] = 0.0; }

    // Calculate the lapse from the redshift function alpha = exp(Phi)
    wormhole_lapse = exp(phi_0);
}
#endif /* WORMHOLE_IMPL_HPP_ */