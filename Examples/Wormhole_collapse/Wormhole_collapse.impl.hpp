#if !defined(WORMHOLE_COLLAPSE_HPP_)
#error "This file should only be included through Wormhole_collapse.hpp"
#endif

#ifndef WORMHOLE_COLLAPSE_IMPL_HPP_
#define WORMHOLE_COLLAPSE_IMPL_HPP_

#include "CoordinateTransformations.hpp"
#include "DimensionDefinitions.hpp"
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

    // Calculate BSSN/CCZ4 variables from ADM variables
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

    // Store the computed values
    current_cell.store_vars(vars);
}

template <class data_t>
void Wormhole_collapse::compute_wormhole(Tensor<2, data_t> &spherical_g,
                                Tensor<2, data_t> &spherical_K,
                                data_t &wormhole_lapse,
                                const Coordinates<data_t> &coords) const
{
    // Get parameters
    double b0 = m_params.throat_radius;
    double Rs = m_params.matching_radius;
    double B = m_params.schwarzschild_radius;
    double width = m_params.transition_width;

    // Get coordinates
    data_t r = coords.get_radius();
    data_t r_sq = r * r;

    // 1. Create the smooth blending function (the "dimmer switch")
    data_t transition_arg = (r - Rs) / width;
    data_t transition_func = 0.5 * (1.0 - tanh(transition_arg));

    // 2. Define the two different shape functions b(r)
    data_t b_wormhole = (b0 * b0) / r;   // Wormhole b(r)
    data_t b_schwarzschild = B;         // Schwarzschild b(r) = const

    // 3. Blend them using the transition function to get the final b(r)
    data_t b_r = transition_func * b_wormhole + (1.0 - transition_func) * b_schwarzschild;
    
    // 4. Calculate g_rr from the final blended b(r)
    data_t b_over_r = b_r / r;
    data_t g_rr_blended = 1.0 / (1.0 - b_over_r + 1e-12);
    data_t g_rr_flat = 1.0;
    auto outside_throat = simd_compare_gt(r, data_t(b0));
    data_t g_rr = simd_conditional(outside_throat, g_rr_blended, g_rr_flat);

    // 5. Define the two different redshift functions Phi(r)
    data_t phi_wormhole = 0.0;
    // For r >> B, log(1-B/r) ≈ -B/r. This goes to 0 correctly.
    data_t phi_schwarzschild = 0.5 * log(1.0 - B / r + 1e-12);

    // 6. Blend them to get the final lapse
    data_t phi_final = transition_func * phi_wormhole + (1.0 - transition_func) * phi_schwarzschild;
    wormhole_lapse = exp(phi_final);

    // --- Fill the metric tensors ---
    data_t rho_sq = coords.x * coords.x + coords.y * coords.y;
    data_t sin_theta_sq = rho_sq / simd_max(r_sq, 1e-12);

    // The metric components in spherical coordinates (r, theta, phi)

    FOR(i, j) { spherical_g[i][j] = 0.0; }
    spherical_g[0][0] = g_rr;
    spherical_g[1][1] = r_sq;
    spherical_g[2][2] = r_sq * sin_theta_sq;

    FOR(i, j) { spherical_K[i][j] = 0.0; }
}

#endif /* WORMHOLE_COLLAPSE_IMPL_HPP_ */