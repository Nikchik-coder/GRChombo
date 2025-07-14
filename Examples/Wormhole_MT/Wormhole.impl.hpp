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
    double b0 = m_params.throat_radius;
    double Phi0 = m_params.redshift_constant;
    double eta2 = m_params.regularization_radius * m_params.regularization_radius;

    // The standard radial coordinate 'r' in terms of Cartesian grid coordinates
    data_t r2 = coords.x * coords.x + coords.y * coords.y + coords.z * coords.z;
    data_t r = sqrt(r2);

    // Your proper distance coordinate 'l', regularized to avoid issues at r=0
    data_t r2_reg = r2 + eta2; // Use a regularized r to calculate l
    data_t l2 = simd_max(r2_reg - b0*b0, 1e-6); // l^2 must be positive
    data_t l = sqrt(l2);

    // BSSN variables to be calculated
    Vars<data_t> vars;

    // --- Correct Implementation of the Wormhole Metric in Cartesian Coordinates ---

    // 2. Construct the physical spatial metric gamma_ij from the line element
    //    dl^2 = dl^2 + (l^2 + b0^2) dOmega^2 = dl^2 + r^2 dOmega^2
    //    The Cartesian form is: gamma_ij = delta_ij + n_i*n_j * (l^2 / r^2)
    //    where n_i = x_i/r is the unit radial vector.
    
    Tensor<2, data_t> gamma;
    
    // This term appears in the metric: (l^2 / r^2)
    // We add epsilon to r2 to avoid division by zero at the exact center.
    data_t radial_term = l2 / (r2 + 1e-6);

    // The unit radial vector n_i = x_i / r
    // We use a regularized r here as well to be safe.
    data_t r_reg = sqrt(r2_reg);
    data_t n_x = coords.x / r_reg;
    data_t n_y = coords.y / r_reg;
    data_t n_z = coords.z / r_reg;
    
    // Construct gamma_ij = delta_ij + n_i*n_j * (l^2/r^2)
    gamma[0][0] = 1.0 + n_x * n_x * radial_term;
    gamma[0][1] =       n_x * n_y * radial_term;
    gamma[0][2] =       n_x * n_z * radial_term;
    gamma[1][1] = 1.0 + n_y * n_y * radial_term;
    gamma[1][2] =       n_y * n_z * radial_term;
    gamma[2][2] = 1.0 + n_z * n_z * radial_term;
    gamma[1][0] = gamma[0][1];
    gamma[2][0] = gamma[0][2];
    gamma[2][1] = gamma[1][2];

    // 3. From the physical metric, derive the BSSN variables chi and h_ij.
    
    // Conformal factor chi = (det(gamma))^(-1/3)
    data_t det_gamma = TensorAlgebra::compute_determinant(gamma);
    vars.chi = pow(det_gamma, -1.0 / 3.0);

    // Conformal metric h_ij = chi * gamma_ij
    FOR(i, j)
    {
        vars.h[i][j] = vars.chi * gamma[i][j];
    }

    // 4. Set the gauge variables and initial impulse
    vars.lapse = exp(Phi0); // Lapse is constant
    FOR(i) { vars.shift[i] = 0.0; } // No initial shift
    FOR(i,j) { vars.A[i][j] = 0.0; } // Trace-free part is zero

    // 5. Set the initial "squeeze" for collapse via the trace of K
    data_t K_profile = m_params.K_amplitude * exp(-r2 / (m_params.K_width * m_params.K_width));
    vars.K = K_profile;

    // 6. Store all the calculated BSSN variables
    current_cell.store_vars(vars);
}

#endif /* WORMHOLE_IMPL_HPP_ */