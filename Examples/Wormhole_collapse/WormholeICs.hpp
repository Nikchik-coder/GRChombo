// In WormholeICs.hpp
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

class WormholeICs
{
  public:
    struct params_t
    {
        double amplitude; // Amplitude of the Gaussian perturbation
        double width;     // Width of the Gaussian perturbation
        std::array<double, CH_SPACEDIM> center;
    };

    WormholeICs(const params_t a_params, double a_dx)
        : m_params(a_params), m_dx(a_dx) {}

    template <class data_t> void compute(Cell<data_t> current_cell) const;

  protected:
    const params_t m_params;
    const double m_dx;
};

template <class data_t>
void WormholeICs::compute(Cell<data_t> current_cell) const
{
    Coordinates<data_t> coords(current_cell, m_dx, m_params.center);
    data_t r = coords.get_radius();

    // Start with flat space and add a Gaussian perturbation to chi
    // This represents a localized lump of "non-flatness" that will evolve.
    data_t A = m_params.amplitude;
    data_t sigma = m_params.width;
    data_t chi = 1.0 + A * exp(-r * r / (sigma * sigma));
    
    // Flat space values for everything else (time-symmetric)
    data_t h11 = 1.0; data_t h12 = 0.0; data_t h13 = 0.0;
    data_t h22 = 1.0; data_t h23 = 0.0; data_t h33 = 1.0;
    
    data_t K = 0.0;
    data_t A11 = 0.0; data_t A12 = 0.0; data_t A13 = 0.0;
    data_t A22 = 0.0; data_t A23 = 0.0; data_t A33 = 0.0;
    
    data_t lapse = 1.0;
    data_t shift1 = 0.0, shift2 = 0.0, shift3 = 0.0;
    data_t B1 = 0.0, B2 = 0.0, B3 = 0.0;
    
    // We need to set Gamma^i correctly for the non-trivial chi
    // Gamma^i = -h^{jk} d_k h_{ij} / 2
    // Since h_ij = delta_ij, this simplifies to Gamma^i = 0
    // But for CCZ4, we need to set Theta = d_i Gamma^i = 0
    data_t Theta = 0.0;
    data_t Gamma1 = 0.0, Gamma2 = 0.0, Gamma3 = 0.0;
    
    // Matter content: negligible scalar field
    data_t phi = 1e-12;
    data_t Pi = 0.0;

    // Store all the variables
    current_cell.store_vars(chi, c_chi);
    current_cell.store_vars(h11, c_h11); current_cell.store_vars(h12, c_h12); current_cell.store_vars(h13, c_h13);
    current_cell.store_vars(h22, c_h22); current_cell.store_vars(h23, c_h23); current_cell.store_vars(h33, c_h33);
    current_cell.store_vars(K, c_K);
    current_cell.store_vars(A11, c_A11); current_cell.store_vars(A12, c_A12); current_cell.store_vars(A13, c_A13);
    current_cell.store_vars(A22, c_A22); current_cell.store_vars(A23, c_A23); current_cell.store_vars(A33, c_A33);
    current_cell.store_vars(lapse, c_lapse);
    current_cell.store_vars(shift1, c_shift1); current_cell.store_vars(shift2, c_shift2); current_cell.store_vars(shift3, c_shift3);
    current_cell.store_vars(B1, c_B1); current_cell.store_vars(B2, c_B2); current_cell.store_vars(B3, c_B3);
    current_cell.store_vars(Theta, c_Theta);
    current_cell.store_vars(Gamma1, c_Gamma1); current_cell.store_vars(Gamma2, c_Gamma2); current_cell.store_vars(Gamma3, c_Gamma3);
    current_cell.store_vars(phi, c_phi);
    current_cell.store_vars(Pi, c_Pi);
}

#endif /* WORMHOLEICS_HPP_ */