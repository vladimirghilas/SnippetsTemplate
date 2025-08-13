function isPalindrome(str) {
  const word = str.split("").reverse().join("");
  return str === word
}

console.log(isPalindrome("level")); // true
console.log(isPalindrome("hello")); // false