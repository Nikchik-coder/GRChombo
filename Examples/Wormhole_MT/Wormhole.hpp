// In Examples/Wormhole_MT/Wormhole.hpp

#ifndef WORMHOLE_HPP_
#define WORMHOLE_HPP_

#include "ADMConformalVars.hpp"
#include "Cell.hpp"
#include "Coordinates.hpp"
#include "Tensor.hpp"
#include "UserVariables.hpp"
#include "VarsTools.hpp"
#include "simd.hpp"

// Define the class for the Wormhole initial data
class Wormhole
{
  public:
    template <class data_t>
    using Vars = ADMConformalVars::VarsWithGauge<data_t>;

    // Struct to hold the parameters for the wormhole
    struct params_t
    {
        double throat_radius;
        double redshift_constant;
        double K_amplitude;
        double K_width;
        std::array<double, CH_SPACEDIM> center;
    };

  protected:
    double m_dx;
    const params_t m_params;

  public:
    // Constructor
    Wormhole(params_t a_params, double a_dx)
        : m_dx(a_dx), m_params(a_params)
    {
    }

    // The function that calculates the initial data
    template <class data_t> void compute(Cell<data_t> current_cell) const;
};

// Include the implementation file
#include "Wormhole.impl.hpp"

#endif /* WORMHOLE_HPP_ */