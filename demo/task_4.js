const fruits = ["apple", "banana"];

function createObjectFromKeys(arr) {
  let result = {};
  for (let key of arr){
        result[key] = key.length
  }
  return result;
}

console.log(createObjectFromKeys(fruits));
// Ожидаемый результат: { apple: 5, banana: 6 }