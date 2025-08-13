const students = [
  { name: "Alice", grades: [90, 85, 95] },
  { name: "Bob", grades: [75, 80, 70] },
  { name: "Charlie", grades: [100, 90, 95] }
];
const result = {}

for (student of students){
    const sum = student.grades.reduce((acc, grade) => acc + grade,0);
    const average = sum/student.grades.length;
    result[student.name] = Math.round(average);
}

console.log(result);
/*
Ожидаемый результат:
{
  Alice: 90,
  Bob: 75,
  Charlie: 95
}
*/