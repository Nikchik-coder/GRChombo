      
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
    data_t l = coords.get_radius(); // The radial coordinate
    double b0 = m_params.throat_radius;
    double Phi0 = m_params.redshift_constant;
    double eta = m_params.regularization_radius; // A small radius to smooth the geometry at the origin

    // BSSN variables to be calculated
    Vars<data_t> vars;

    // --- CORRECTED Implementation of the Regularized Morris-Thorne Metric ---

    // 2. Calculate the components of the physical spatial metric gamma_ij
    data_t l2 = l * l;
    double b02 = b0 * b0;
    
    // Regularize the radius to avoid division by zero at the origin.
    data_t l2_reg = l2 + eta * eta;
    data_t l4_reg = l2_reg * l2_reg;

    Tensor<2, data_t> gamma; // The physical spatial metric
    
    // Store Cartesian coordinates in an array for easy looping
    std::array<data_t, CH_SPACEDIM> cart_coords;
    cart_coords[0] = coords.x;
    cart_coords[1] = coords.y;
    cart_coords[2] = coords.z;
    
    FOR(i, j)
    {
        // This is the correct Cartesian form of the Morris-Thorne spatial metric.
        // CORRECTED: Access coordinates directly with cart_coords[i] instead of a non-existent function.
        gamma[i][j] = (i == j) + (cart_coords[i] * cart_coords[j] / l4_reg) * b02;
    }

    // 3. From the physical metric, derive the BSSN variables chi and h_ij.
    
    // Conformal factor chi = (det(gamma))^(-1/3)
    data_t det_gamma = TensorAlgebra::compute_determinant(gamma);
    vars.chi = pow(det_gamma, -1.0 / 3.0);

    // Conformal metric h_ij = chi * gamma_ij
    FOR(i, j)
    {
        vars.h[i][j] = vars.chi * gamma[i][j];
    }

    // 4. Set the lapse, shift, and trace-free extrinsic curvature
    vars.lapse = exp(Phi0); // Lapse is constant from redshift parameter
    FOR(i) { vars.shift[i] = 0.0; } // No initial shift
    FOR(i,j) { vars.A[i][j] = 0.0; } // A_ij is trace-free and zero for a pure-trace initial kick

    // 5. Set the initial "squeeze" for collapse via the trace of the Extrinsic Curvature, K
    data_t K_profile = m_params.K_amplitude * exp(-l2 / (m_params.K_width * m_params.K_width));
    vars.K = K_profile;

    // 6. Store all the calculated BSSN variables into the grid cell
    current_cell.store_vars(vars);
}

#endif /* WORMHOLE_IMPL_HPP_ */

    