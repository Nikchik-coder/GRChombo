// In Examples/Wormhole_collapse/Wormhole_collapse.hpp

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
  public:
    // Define the type for the BSSN variables and gauge
    template <class data_t>
    using Vars = ADMConformalVars::VarsWithGauge<data_t>;

    // Struct for the initial data parameters
    struct params_t
    {
        double mass;                            //!< The mass parameter M of the Schwarzschild solution
        std::array<double, CH_SPACEDIM> center; //!< The center of the grid
    };

  protected:
    double m_dx;
    const params_t m_params;

  public:
    Wormhole_collapse(params_t a_params, double a_dx)
        : m_dx(a_dx), m_params(a_params)
    {
    }

    /// This function computes the BSSN variables for the initial data
    template <class data_t> void compute(Cell<data_t> current_cell) const;
};

#include "Wormhole_collapse.impl.hpp"

#endif /* WORMHOLE_COLLAPSE_HPP_ */