function countWords(sentence) {
  const words = sentence.split(" ");
  const counts = {};
  for (word of words){
      if (counts[word]){
          counts[word] += 1
      }else{
          counts[word] = 1
      }
  }
  return counts
}

const sentence = "hello world hello";
console.log(countWords(sentence));
// Ожидаемый результат: { hello: 2, world: 1 }