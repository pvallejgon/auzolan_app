import { Form } from 'react-bootstrap'
import { CATEGORIES } from '../data/categories.js'

export default function RequestFilters({ status, category, onChange }) {
  return (
    <div className="filter-row">
      <span className="muted">Filtrar por:</span>
      <Form.Select
        name="status"
        value={status}
        onChange={onChange}
        className="filter-select"
        style={{ minWidth: 180 }}
      >
        <option value="">Todos los estados</option>
        <option value="open">Abierta</option>
        <option value="in_progress">En progreso</option>
        <option value="resolved">Resuelta</option>
        <option value="cancelled">Cancelada</option>
      </Form.Select>
      <Form.Select
        name="category"
        value={category}
        onChange={onChange}
        className="filter-select"
        style={{ minWidth: 220 }}
      >
        <option value="">Todas las categorías</option>
        {CATEGORIES.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </Form.Select>
    </div>
  )
}
