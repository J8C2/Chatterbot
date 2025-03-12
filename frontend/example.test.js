const { getResponse } = require('./chatbot'); // Assuming `getResponse` is the function handling queries

// Testing the chatbot to see if the response is as expected
test('Chatbot responds correctly to lunch menu query', () => {
    // Sample query for the chatbot
    const query = "What is the school lunch menu today?";
    // The expected response to compare the chatbot's repsonse to
    const expectedResponse = "Today's lunch menu is: Pizza, Salad, and Fruit.";
    // Send the query to the chatbot and retrieve it's response
    const response = getResponse(query);
    // Assert that the actual resposne matches the expected response
    expect(response).toBe(expectedResponse);
});
