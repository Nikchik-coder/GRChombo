// In Examples/Wormhole/Wormhole.hpp

#ifndef WORMHOLE_COLLAPSE_HPP_
#define WORMHOLE_COLLAPSE_HPP_

#include "ADMConformalVars.hpp"
#include "Cell.hpp"
#include "Coordinates.hpp"
#include "Tensor.hpp"
#include "UserVariables.hpp"
#include "VarsTools.hpp"
#include "simd.hpp"

class Wormhole_collapse
{
    template <class data_t>
    using Vars = ADMConformalVars::VarsWithGauge<data_t>;

  public:
    struct params_t
    {
        double throat_radius;                   //!< The radius of the wormhole throat, b0
        double redshift_constant;               //!< The constant value for the redshift function Phi
        std::array<double, CH_SPACEDIM> center; //!< The center of the wormhole
    };

  protected:
    double m_dx;
    params_t m_params;

  public:
    Wormhole_collapse(params_t a_params, double a_dx) : m_dx(a_dx), m_params(a_params) {}

    // Main function to calculate and fill variables for a cell
    template <class data_t> void compute(Cell<data_t> current_cell) const;

  protected:
    // Helper function to compute metric components in spherical coordinates
    // --- MODIFIED: Now also computes the lapse ---
    template <class data_t>
    void compute_wormhole(
        Tensor<2, data_t> &spherical_g, 
        Tensor<2, data_t> &spherical_K,
        data_t &wormhole_lapse,
        const Coordinates<data_t> &coords) const;
};

#include "Wormhole_collapse.impl.hpp"

#endif /* WORMHOLE_COLLAPSE_HPP_ */  