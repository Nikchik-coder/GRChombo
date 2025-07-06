/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

#ifndef WORMHOLEICS_HPP_
#define WORMHOLEICS_HPP_

#include "Cell.hpp"
#include "Coordinates.hpp"
#include "MatterCCZ4RHS.hpp"
#include "ScalarField.hpp"
#include "Tensor.hpp"
#include "UserVariables.hpp"
#include "VarsTools.hpp"
#include "simd.hpp"

//! Class which sets the initial conditions for a collapsing Morris-Thorne wormhole.
//! This setup is time-symmetric (K=0) and supported by a negligible scalar field,
//! so it is expected to be unstable and collapse, forming black holes.
class WormholeICs
{
  public:
    // Parameters for the wormhole
    struct params_t
    {
        double throat_radius;    // The parameter b_0 for the throat size
        double mass;             // An unused mass parameter for now
        double scalar_amplitude; // Amplitude of the negligible scalar field
        std::array<double, CH_SPACEDIM> center;
    };

    // Constructor
    WormholeICs(const params_t a_params, double a_dx)
        : m_params(a_params), m_dx(a_dx)
    {
    }

    // The main compute function that sets the variables on the grid
    template <class data_t> void compute(Cell<data_t> current_cell) const;

  protected:
    const params_t m_params;
    const double m_dx;
};

template <class data_t>
void WormholeICs::compute(Cell<data_t> current_cell) const
{
    // Get the coordinates of the current cell, centered on the wormhole
    Coordinates<data_t> coords(current_cell, m_dx, m_params.center);
    data_t x = coords.x;
    data_t y = coords.y;
    data_t z = coords.z;
    
    // Use a regularized radius to avoid singularity at the center
    data_t r = coords.get_radius();
    r = sqrt(r * r + 1e-6); // Small regularization

    // Wormhole metric parameters from the simplified Morris-Thorne solution
    // ds^2 = -dt^2 + dr^2/(1-b_0/r) + r^2*dOmega^2
    // We set the redshift function Phi(r) = 0, so lapse = 1.
    // We use a simple shape function b(r) = b_0.
    data_t b_0 = m_params.throat_radius;
    
    // The g_rr component of the metric in spherical coordinates
    // We must regularize this to avoid division by zero at the throat r = b_0
    data_t one_minus_b_over_r = 1.0 - b_0 / r;
    one_minus_b_over_r = simd_max(one_minus_b_over_r, 1e-6); // Prevent division by zero
    data_t g_rr_spher = 1.0 / one_minus_b_over_r;

    // The spatial metric in Cartesian coordinates is given by:
    // g_ij = delta_ij + (g_rr - 1) * n_i * n_j
    // where n_i = x_i / r is the radial unit vector.
    data_t nx = x / r;
    data_t ny = y / r;
    data_t nz = z / r;
    
    data_t g_xx = 1.0 + (g_rr_spher - 1.0) * nx * nx;
    data_t g_yy = 1.0 + (g_rr_spher - 1.0) * ny * ny;
    data_t g_zz = 1.0 + (g_rr_spher - 1.0) * nz * nz;
    data_t g_xy = (g_rr_spher - 1.0) * nx * ny;
    data_t g_xz = (g_rr_spher - 1.0) * nx * nz;
    data_t g_yz = (g_rr_spher - 1.0) * ny * nz;

    // Calculate the determinant of the spatial metric
    data_t det_gamma = TensorAlgebra::compute_determinant(g_xx, g_xy, g_xz, g_yy, g_yz, g_zz);
    det_gamma = simd_max(det_gamma, 1e-12); // Ensure determinant is positive

    // The conformal factor chi and the conformal metric h_ij
    data_t chi = pow(det_gamma, -1.0 / 3.0);
    
    // h_ij = chi * g_ij
    data_t h11 = chi * g_xx;
    data_t h12 = chi * g_xy;
    data_t h13 = chi * g_xz;
    data_t h22 = chi * g_yy;
    data_t h23 = chi * g_yz;
    data_t h33 = chi * g_zz;

    // Time-symmetric initial conditions: K_ij = 0
    // This implies the trace K=0 and the trace-free part A_ij=0
    data_t K = 0.0;
    data_t A11 = 0.0; data_t A12 = 0.0; data_t A13 = 0.0;
    data_t A22 = 0.0; data_t A23 = 0.0; data_t A33 = 0.0;
    
    // Matter content: a negligible scalar field to make the setup non-vacuum
    // This avoids needing exotic matter, and the instability should drive collapse.
    data_t phi = m_params.scalar_amplitude;
    data_t Pi = 0.0; // No initial momentum
    
    // CCZ4 variables
    data_t lapse = 1.0;
    data_t shift1 = 0.0, shift2 = 0.0, shift3 = 0.0;
    data_t Theta = 0.0;
    data_t Gamma1 = 0.0, Gamma2 = 0.0, Gamma3 = 0.0;
    data_t B1 = 0.0, B2 = 0.0, B3 = 0.0;

    // Store all the variables
    current_cell.store_vars(chi, c_chi);
    current_cell.store_vars(h11, c_h11);
    current_cell.store_vars(h12, c_h12);
    current_cell.store_vars(h13, c_h13);
    current_cell.store_vars(h22, c_h22);
    current_cell.store_vars(h23, c_h23);
    current_cell.store_vars(h33, c_h33);
    current_cell.store_vars(K, c_K);
    current_cell.store_vars(A11, c_A11);
    current_cell.store_vars(A12, c_A12);
    current_cell.store_vars(A13, c_A13);
    current_cell.store_vars(A22, c_A22);
    current_cell.store_vars(A23, c_A23);
    current_cell.store_vars(A33, c_A33);
    current_cell.store_vars(lapse, c_lapse);
    current_cell.store_vars(shift1, c_shift1);
    current_cell.store_vars(shift2, c_shift2);
    current_cell.store_vars(shift3, c_shift3);
    current_cell.store_vars(B1, c_B1);
    current_cell.store_vars(B2, c_B2);
    current_cell.store_vars(B3, c_B3);
    current_cell.store_vars(Theta, c_Theta);
    current_cell.store_vars(Gamma1, c_Gamma1);
    current_cell.store_vars(Gamma2, c_Gamma2);
    current_cell.store_vars(Gamma3, c_Gamma3);
    current_cell.store_vars(phi, c_phi);
    current_cell.store_vars(Pi, c_Pi);
}

#endif /* WORMHOLEICS_HPP_ */