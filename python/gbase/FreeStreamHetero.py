from gbase.GenStreaming import GenStreaming
import math


class FreeStreamHetero(GenStreaming):
    AIR_MATERIAL_ID = 1

    def add_streaming_mobile_particles(self):
        super().add_streaming_mobile_particles()
        return self.add_air_particles()

    def material_mass(self, material_id):
        return float(self.material_properties_by_id[material_id]["relative_mass"])

    def material_cell_density(self, material_id):
        return float(self.material_properties_by_id[material_id].get("cell_density", 0.0))

    def air_fill_velocity(self):
        raw_velocity = self.itemcfg.get("air_initial_particle_velocity", (0.0, 0.0, 0.0))
        if len(raw_velocity) != 3:
            raise ValueError("air_initial_particle_velocity must contain 3 values")
        try:
            velocity = tuple(float(value) for value in raw_velocity)
        except (TypeError, ValueError) as error:
            raise ValueError("air_initial_particle_velocity values must be numeric") from error
        if not all(math.isfinite(value) for value in velocity):
            raise ValueError("air_initial_particle_velocity values must be finite")
        return velocity

    def air_fill_cell_range(self):
        raw_bounds = self.itemcfg.get("air_fill_bounds")
        if raw_bounds is None:
            raw_bounds = self.death_bounds[:4]
        if len(raw_bounds) != 4:
            raise ValueError("air_fill_bounds must contain 4 values")
        try:
            x_min, x_max, y_min, y_max = (float(value) for value in raw_bounds)
        except (TypeError, ValueError) as error:
            raise ValueError("air_fill_bounds values must be numeric") from error
        if not all(math.isfinite(value) for value in (x_min, x_max, y_min, y_max)):
            raise ValueError("air_fill_bounds values must be finite")
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("air_fill_bounds min values must be less than max values")
        x_first = int(math.ceil(x_min))
        x_last_exclusive = int(math.floor(x_max))
        y_first = int(math.ceil(y_min))
        y_last_exclusive = int(math.floor(y_max))
        return range(x_first, x_last_exclusive), range(y_first, y_last_exclusive)

    def cell_slot_centers(self, cell_index):
        radius = float(self.radius)
        spacing = float(self.particle_center_spacing)
        inner_min = float(cell_index) + radius
        inner_max = float(cell_index + 1) - radius
        usable = inner_max - inner_min
        if usable < 0.0:
            return ()
        count = int(math.floor((usable / spacing) + 1.0e-12)) + 1
        if count <= 1:
            return (0.5 * (inner_min + inner_max),)
        occupied = (count - 1) * spacing
        first = inner_min + 0.5 * (usable - occupied)
        return tuple(first + index * spacing for index in range(count))

    def selected_slots(self, slots, selected_count):
        if selected_count <= 0:
            return ()
        if selected_count >= len(slots):
            return slots
        if selected_count == 1:
            return (slots[len(slots) // 2],)
        last = len(slots) - 1
        used_indices = set()
        selected = []
        for index in range(selected_count):
            slot_index = int(round(index * last / (selected_count - 1)))
            while slot_index in used_indices and slot_index < last:
                slot_index += 1
            while slot_index in used_indices and slot_index > 0:
                slot_index -= 1
            used_indices.add(slot_index)
            selected.append(slots[slot_index])
        return tuple(selected)

    def add_air_particles(self):
        material_id = self.AIR_MATERIAL_ID
        if material_id not in self.material_properties_by_id:
            return 0

        cell_density = self.material_cell_density(material_id)
        if cell_density <= 0.0:
            return 0

        velocity = self.air_fill_velocity()
        mass = self.material_mass(material_id)
        x_cells, y_cells = self.air_fill_cell_range()
        first_particle = self.number_active_particles + 1
        cells_filled = 0
        total_slots = 0

        for cell_x in x_cells:
            x_centers = self.cell_slot_centers(cell_x)
            for cell_y in y_cells:
                y_centers = self.cell_slot_centers(cell_y)
                slots = tuple((x, y) for y in y_centers for x in x_centers)
                slot_count = len(slots)
                if slot_count == 0:
                    continue
                selected_count = int(math.floor(cell_density * slot_count + 1.0e-12))
                if selected_count == 0 and cell_density > 0.0:
                    selected_count = 1
                for x_center, y_center in self.selected_slots(slots, selected_count):
                    self.add_mobile_particle(
                        (x_center, y_center, self.particle_plane_z),
                        velocity,
                        radius=self.radius,
                        mass=mass,
                        material_id=material_id,
                        collision_stiffness_q=float(
                            self.itemcfg.get("collision_stiffness_q", 0.0)
                        ),
                    )
                cells_filled += 1
                total_slots += slot_count

        air_count = self.number_active_particles - first_particle + 1
        report_text = (
            "Air material fill report:\n"
            f"  material_id: {material_id}\n"
            f"  cell_density: {cell_density:g}\n"
            f"  cell count: {cells_filled}\n"
            f"  available slots: {total_slots}\n"
            f"  air particles: {air_count}\n"
            f"  mass: {mass:g}\n"
            f"  velocity: {velocity}"
        )
        print(report_text)
        self.write_validation_log(report_text)
        return air_count
