from database import Database
assert Database.calculate_next_cold_pressure(1.35,1.86,1.80)==(0.06,1.29)
assert Database.calculate_next_cold_pressure(1.35,1.74,1.80)==(-0.06,1.41)
print("OK")
