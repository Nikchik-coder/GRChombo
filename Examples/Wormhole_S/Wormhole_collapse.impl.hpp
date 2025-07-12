// In Examples/Wormhole_collapse/Wormhole_collapse.impl.hpp

#if !defined(WORMHOLE_COLLAPSE_HPP_)
#error "This file should only be included through Wormhole_collapse.hpp"
#endif

#ifndef WORMHOLE_COLLAPSE_IMPL_HPP_
#define WORMHOLE_COLLAPSE_IMPL_HPP_

#include "DimensionDefinitions.hpp"
#include "TensorAlgebra.hpp"
#include "simd.hpp"

// This is the main compute function called for each cell
template <class data_t>
void Wormhole_collapse::compute(Cell<data_t> current_cell) const
{
    using namespace TensorAlgebra;

    // Get the coordinates and compute the isotropic radius
    Coordinates<data_t> coords(current_cell, m_dx, m_params.center);
    data_t M = m_params.mass;
    data_t rho = coords.get_radius(); // This is the isotropic radius

    // A small number to avoid division by zero at the puncture r=0
    const double epsilon = 1e-6;
    rho = simd_max(rho, epsilon);

    // Calculate the conformal factor psi for isotropic coordinates
    data_t psi = 1.0 + M / (2.0 * rho);
    data_t psi_4 = pow(psi, 4);

    // The BSSN variables for a time-symmetric Schwarzschild solution
    Vars<data_t> vars;

    // 1. Conformal metric is flat: h_ij = delta_ij
    FOR(i, j) { vars.h[i][j] = (i == j) ? 1.0 : 0.0; }

    // 2. Conformal factor: chi = psi^(-4)
    vars.chi = 1.0 / psi_4;

    // 3. Extrinsic curvature K and A_ij are zero for a time-symmetric slice
    vars.K = 0.0;
    FOR(i, j) { vars.A[i][j] = 0.0; }

    // 4. Lapse: alpha = (1 - M / 2rho) / (1 + M / 2rho)
    data_t alpha_numerator = 1.0 - M / (2.0 * rho);
    data_t alpha_denominator = 1.0 + M / (2.0 * rho);
    vars.lapse = alpha_numerator / alpha_denominator;
    vars.lapse = simd_max(vars.lapse, epsilon); // Prevent negative/zero lapse

    // 5. Shift is zero
    FOR(i) { vars.shift[i] = 0.0; }

    // 6. Gamma^i (connection functions) are calculated numerically by GRChombo later.

    // Store the computed values
    current_cell.store_vars(vars);
}

#endif /* WORMHOLE_COLLAPSE_IMPL_HPP_ */