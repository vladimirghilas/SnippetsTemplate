function countVowels(str) {
  const vowels = "aeiou";
  let numVowels = 0
  for (let char of str){
      if (vowels.includes(char)){
          numVowels++;
      }
  }
  return numVowels;
}

console.log(countVowels("hello world"))