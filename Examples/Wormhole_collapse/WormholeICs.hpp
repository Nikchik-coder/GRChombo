/* GRChombo
 * Copyright 2012 The GRChombo collaboration.
 * Please refer to LICENSE in GRChombo's root directory.
 */

#ifndef WORMHOLEICS_HPP_
#define WORMHOLEICS_HPP_

#include "Cell.hpp"
#include "Coordinates.hpp"
#include "MatterCCZ4RHS.hpp"
#include "Potential.hpp"
#include "ScalarField.hpp"
#include "Tensor.hpp"
#include "UserVariables.hpp" //This files needs NUM_VARS - total no. components
#include "VarsTools.hpp"
#include "simd.hpp"

//! Class which sets the initial Morris-Thorne wormhole config (without exotic matter)
class WormholeICs
{
public:
    // Define parameters for Morris-Thorne wormhole
    struct params_t
    {
        double throat_radius;      // b_0 - throat radius
        double mass;              // M - wormhole mass parameter
        double scalar_amplitude;   // tiny scalar field (essentially zero)
        std::array<double, CH_SPACEDIM> center;
    };

    // Constructor
    WormholeICs(const params_t a_params, double a_dx)
        : m_params(a_params), m_dx(a_dx) {}

    // The main compute function
    template <class data_t>
    void compute(Cell<data_t> current_cell) const;

protected:
    const params_t m_params;
    const double m_dx;
    
    // Morris-Thorne shape function b(r)
    template <class data_t>
    data_t shape_function(data_t r) const;
    
    // Morris-Thorne redshift function (for more general case)
    template <class data_t>
    data_t redshift_function(data_t r) const;
};

template <class data_t>
data_t WormholeICs::shape_function(data_t r) const
{
    // Morris-Thorne shape function: b(r) = b_0 * (b_0/r)^n
    // For simplicity, use b(r) = b_0^2/r for r > b_0
    // and b(r) = b_0 for r ≤ b_0
    data_t b_0 = m_params.throat_radius;
    
    // Smooth shape function to avoid singularities
    data_t r_smooth = sqrt(r*r + 0.1*b_0*b_0); // small smoothing
    return b_0*b_0 / r_smooth;
}

template <class data_t>
data_t WormholeICs::redshift_function(data_t r) const
{
    // For simplicity, start with zero redshift function
    // This gives us the simplest Morris-Thorne case
    return 0.0;
}

template <class data_t>
void WormholeICs::compute(Cell<data_t> current_cell) const
{
    // Get the coordinates of the current cell
    Coordinates<data_t> coords(current_cell, m_dx, m_params.center);
    data_t x = coords.x;
    data_t y = coords.y;
    data_t z = coords.z;
    data_t r = coords.get_radius();
    
    // Morris-Thorne wormhole parameters
    data_t b_0 = m_params.throat_radius;
    data_t b_r = shape_function(r);
    data_t Phi_r = redshift_function(r);
    
    // Morris-Thorne metric in spherical coordinates:
    // ds² = -e^(2Φ) dt² + dr²/(1-b(r)/r) + r²(dθ² + sin²θ dφ²)
    // For our case, Φ = 0, so e^(2Φ) = 1
    
    // Convert to 3+1 ADM form
    // ADM lapse: N = e^Φ = 1 (since Φ = 0)
    data_t lapse = 1.0;
    
    // ADM shift: N^i = 0 (spherically symmetric, time-symmetric)
    data_t shift1 = 0.0;
    data_t shift2 = 0.0;
    data_t shift3 = 0.0;
    
    // Spatial metric components in Cartesian coordinates
    // We need to transform from spherical Morris-Thorne to Cartesian
    
    // In spherical coordinates:
    // g_rr = 1/(1-b(r)/r)
    // g_θθ = r²
    // g_φφ = r²sin²θ
    
    // Transformation to Cartesian coordinates
    data_t sin_theta = sqrt(x*x + y*y) / r;
    data_t cos_theta = z / r;
    data_t sin_phi = (r > 1e-10) ? y / sqrt(x*x + y*y + 1e-20) : 0.0;
    data_t cos_phi = (r > 1e-10) ? x / sqrt(x*x + y*y + 1e-20) : 1.0;
    
    // Avoid singularities at the origin
    if (r < 1e-10) {
        sin_theta = 0.0;
        cos_theta = 1.0;
        sin_phi = 0.0;
        cos_phi = 1.0;
    }
    
    // Radial direction unit vector
    data_t e_r_x = sin_theta * cos_phi;
    data_t e_r_y = sin_theta * sin_phi;
    data_t e_r_z = cos_theta;
    
    // Theta direction unit vector
    data_t e_theta_x = cos_theta * cos_phi;
    data_t e_theta_y = cos_theta * sin_phi;
    data_t e_theta_z = -sin_theta;
    
    // Phi direction unit vector
    data_t e_phi_x = -sin_phi;
    data_t e_phi_y = cos_phi;
    data_t e_phi_z = 0.0;
    
    // Metric components in spherical coordinates
    data_t g_rr = 1.0 / (1.0 - b_r/r);
    data_t g_theta_theta = r*r;
    data_t g_phi_phi = r*r * sin_theta*sin_theta;
    
    // Transform to Cartesian coordinates
    data_t g_xx = g_rr * e_r_x * e_r_x + g_theta_theta * e_theta_x * e_theta_x + g_phi_phi * e_phi_x * e_phi_x;
    data_t g_yy = g_rr * e_r_y * e_r_y + g_theta_theta * e_theta_y * e_theta_y + g_phi_phi * e_phi_y * e_phi_y;
    data_t g_zz = g_rr * e_r_z * e_r_z + g_theta_theta * e_theta_z * e_theta_z + g_phi_phi * e_phi_z * e_phi_z;
    
    data_t g_xy = g_rr * e_r_x * e_r_y + g_theta_theta * e_theta_x * e_theta_y + g_phi_phi * e_phi_x * e_phi_y;
    data_t g_xz = g_rr * e_r_x * e_r_z + g_theta_theta * e_theta_x * e_theta_z + g_phi_phi * e_phi_x * e_phi_z;
    data_t g_yz = g_rr * e_r_y * e_r_z + g_theta_theta * e_theta_y * e_theta_z + g_phi_phi * e_phi_y * e_phi_z;
    
    // Compute conformal factor χ = (det γ)^(-1/3)
    data_t det_gamma = g_xx * (g_yy * g_zz - g_yz * g_yz) 
                     - g_xy * (g_xy * g_zz - g_yz * g_xz) 
                     + g_xz * (g_xy * g_yz - g_yy * g_xz);
    
    // Avoid division by zero
    det_gamma = max(det_gamma, 1e-12);
    data_t chi = pow(det_gamma, -1.0/3.0);
    
    // Conformal metric h_ij = χ * γ_ij
    data_t h11 = chi * g_xx;
    data_t h12 = chi * g_xy;
    data_t h13 = chi * g_xz;
    data_t h22 = chi * g_yy;
    data_t h23 = chi * g_yz;
    data_t h33 = chi * g_zz;
    
    // Extrinsic curvature - start with zero (time-symmetric slice)
    // The wormhole will collapse due to lack of exotic matter
    data_t K = 0.0;
    data_t A11 = 0.0;
    data_t A12 = 0.0;
    data_t A13 = 0.0;
    data_t A22 = 0.0;
    data_t A23 = 0.0;
    data_t A33 = 0.0;
    
    // Scalar field matter - essentially zero (no exotic matter)
    data_t phi = m_params.scalar_amplitude * exp(-r*r/(10.0*b_0*b_0));
    data_t Pi = 0.0; // Zero momentum
    
    // Store values in the cell
    current_cell.store_vars(lapse, c_lapse);
    current_cell.store_vars(shift1, c_shift1);
    current_cell.store_vars(shift2, c_shift2);
    current_cell.store_vars(shift3, c_shift3);
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
    current_cell.store_vars(phi, c_phi);
    current_cell.store_vars(Pi, c_Pi);
}

#endif /* WORMHOLEICS_HPP_ */
